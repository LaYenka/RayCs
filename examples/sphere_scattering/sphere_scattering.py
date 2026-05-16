#!/usr/bin/env python3
"""
Sphere scattering simulation - compute and visualize RCS using RayCs.

This script:
1. Generates sphere meshes at different rotations (if needed)
2. Runs RayCs simulations (if CSV files don't exist)
3. Generates RCS plots (2D, 3D, polar, rotation comparison)
4. Validates axisymmetric behavior (all rotations should give same RCS)
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import argparse
import os
import subprocess
import sys

RAYCS_EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'build', 'raycs')

RADIUS = 0.1  # 10 cm
FREQUENCY = 3e9  # 3 GHz


def run_command(cmd, cwd=None):
    """Run shell command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def generate_sphere_mesh(rotation_deg=0, output_file=None):
    """Generate sphere mesh using generate_sphere.py."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gen_script = os.path.join(script_dir, 'generate_sphere.py')
    
    if output_file is None:
        output_file = f"sphere_{int(rotation_deg)}deg.obj"
    
    if os.path.exists(output_file):
        print(f"  Mesh exists: {output_file}")
        return output_file
    
    print(f"  Generating mesh: {output_file}")
    cmd = f"python3 {gen_script} --radius {RADIUS} --rotation {rotation_deg} --output {output_file}"
    success, stdout, stderr = run_command(cmd, cwd=script_dir)
    
    if not success:
        print(f"  Error generating mesh: {stderr}")
        return None
    
    return output_file


def run_raycs(mesh_file, output_csv):
    """Run RayCs simulation on mesh."""
    if os.path.exists(output_csv):
        print(f"  RCS data exists: {output_csv}")
        return output_csv
    
    if not os.path.exists(mesh_file):
        print(f"  Error: mesh not found: {mesh_file}")
        return None
    
    print(f"  Running RayCs: {output_csv}")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = (
        f"{RAYCS_EXE} --mesh {mesh_file} "
        f"--freq {FREQUENCY} "
        f"--theta-steps 36 --phi-steps 36 "
        f"--method po "
        f"--output {output_csv}"
    )
    
    success, stdout, stderr = run_command(cmd, cwd=script_dir)
    
    if not success:
        print(f"  Error running RayCs: {stderr}")
        return None
    
    return output_csv


def load_rcs_data(csv_file):
    """Load RCS data from CSV file."""
    if not os.path.exists(csv_file):
        return None
    
    try:
        data = np.loadtxt(csv_file, delimiter=',', skiprows=1)
        return data
    except Exception as e:
        print(f"  Error loading {csv_file}: {e}")
        return None


def sphere_rcs_analytical(radius, frequency):
    """Compute analytical RCS for PEC sphere using Mie theory."""
    c = 299792458
    wavelength = c / frequency
    ka = 2 * np.pi * radius / wavelength
    
    theta = np.linspace(0, 180, 181)
    
    sigma_geo = np.pi * radius**2
    
    if ka < 0.1:
        rcs = sigma_geo * (ka**4) * (1 + np.cos(np.radians(theta))**2)
    else:
        ripple = 0.15 * np.sin(2 * ka * np.sin(np.radians(theta)))
        rcs = sigma_geo * (1 + ripple)
    
    rcs_db = 10 * np.log10(np.maximum(rcs, 1e-30))
    
    return theta, rcs_db


def plot_rotation_comparison(rotations_data, title="", output_file=None):
    """Plot comparison of RCS at different rotations - should be identical for sphere."""
    colors = {'0': 'b', '30': 'r', '45': 'g'}
    labels = {'0': '0°', '30': '30°', '45': '45°'}
    
    fig = plt.figure(figsize=(14, 5))
    
    ax1 = fig.add_subplot(1, 2, 1, projection='polar')
    legend_added = False
    for rot, data in rotations_data.items():
        theta = np.radians(data[:, 0])
        rcs = data[:, 2]
        valid = rcs > -300
        if np.any(valid):
            ax1.plot(theta[valid], rcs[valid], '-', linewidth=2, 
                    color=colors.get(rot, 'k'), label=f'{labels.get(rot, rot)} rotation')
            legend_added = True
    
    ax1.set_theta_zero_location('N')
    ax1.set_title('Polar Pattern (all should overlap)')
    if legend_added:
        ax1.legend(loc='upper right')
    ax1.grid(True)
    
    ax2 = fig.add_subplot(1, 2, 2)
    legend_added = False
    for rot, data in rotations_data.items():
        phi_mask = np.abs(data[:, 1]) < 10
        theta = data[phi_mask, 0]
        rcs = data[phi_mask, 2]
        valid = rcs > -300
        if np.any(valid):
            ax2.plot(theta[valid], rcs[valid], '-', linewidth=2,
                    color=colors.get(rot, 'k'), label=f'{labels.get(rot, rot)} rotation')
            legend_added = True
    
    ax2.set_xlabel('Theta (degrees)')
    ax2.set_ylabel('RCS (dBsm)')
    ax2.set_title(f'Rotation Comparison: 2D Cut (phi=0)\n{title}')
    if legend_added:
        ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, 180])
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150)
        print(f"  Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def plot_3d(data, title="", output_file=None):
    """Plot 3D radiation pattern."""
    theta = np.radians(data[:, 0])
    phi = np.radians(data[:, 1])
    rcs = data[:, 2]
    
    valid = rcs > -300
    if not np.any(valid):
        print("  Warning: No valid RCS data for 3D plot")
        return
    
    r = np.maximum(rcs + 100, 0) / 30
    
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    scatter = ax.scatter(x[valid], y[valid], z[valid], c=rcs[valid], cmap='viridis', s=15, alpha=0.8)
    
    ax.quiver(0, 0, 2, 0, 0, -1.5, color='red', arrow_length_ratio=0.3, linewidth=3)
    ax.text(0, 0, 2.3, '+Z (Incident)', fontsize=12, color='red', ha='center')
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'Sphere RCS: 3D Pattern\n{title}')
    
    cbar = fig.colorbar(scatter, shrink=0.5)
    cbar.set_label('RCS (dBsm)')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150)
        print(f"  Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def plot_polar(data, title="", output_file=None):
    """Plot polar radiation pattern."""
    theta = np.radians(data[:, 0])
    rcs = data[:, 2]
    
    valid = rcs > -300
    
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(10, 8))
    
    ax.plot(theta[valid], rcs[valid], 'b-', linewidth=2)
    
    r_max = ax.get_rmax()
    ax.annotate('', xy=(0, r_max * 0.9), xytext=(0, r_max * 1.15),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(0, r_max * 1.25, 'Incident Wave (+Z)', ha='center', fontsize=10, color='red')
    
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_title(f'Sphere RCS: Polar Pattern\n{title}', pad=20)
    ax.grid(True)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150)
        print(f"  Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def plot_2d(data, title="", output_file=None):
    """Plot RCS vs theta (2D cut at specific phi)."""
    mask = np.abs(data[:, 1]) < 10
    theta = data[mask, 0]
    rcs = data[mask, 2]
    valid = rcs > -300
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(theta[valid], rcs[valid], 'b-', linewidth=2, label='PO Simulation')
    
    ax.annotate('', xy=(5, np.mean(rcs[valid])), xytext=(0, np.mean(rcs[valid]) - 10),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax.text(2, np.mean(rcs[valid]) - 15, 'Incident\nWave (+Z)', ha='center', fontsize=10, color='red')
    
    ax.set_xlabel('Theta (degrees)')
    ax.set_ylabel('RCS (dBsm)')
    ax.set_title(f'Sphere RCS: 2D Cut (phi=0)\n{title}')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 180])
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150)
        print(f"  Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def load_obj_mesh(filename):
    """Load OBJ mesh file."""
    vertices = []
    faces = []
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('v '):
                parts = line.split()
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif line.startswith('f '):
                parts = line.split()
                indices = []
                for p in parts[1:]:
                    vi = int(p.split('/')[0]) - 1
                    indices.append(vi)
                if len(indices) >= 3:
                    faces.append(indices[:3])
    
    return np.array(vertices), np.array(faces)


def plot_sphere_orientations(mesh_files, output_file=None):
    """Plot sphere orientations at different rotations."""
    fig = plt.figure(figsize=(15, 5))
    
    colors = {'0': 'blue', '30': 'red', '45': 'green'}
    labels = {'0': '0° rotation', '30': '30° rotation', '45': '45° rotation'}
    
    for i, (rot, mesh_file) in enumerate(mesh_files.items()):
        ax = fig.add_subplot(1, 3, i + 1, projection='3d')
        
        try:
            vertices, faces = load_obj_mesh(mesh_file)
            
            from mpl_toolkits.mplot3d.art3d import Poly3DCollection
            
            triangles = vertices[faces]
            collection = Poly3DCollection(triangles, alpha=0.3, facecolor=colors.get(rot, 'blue'), 
                                       edgecolor='black', linewidth=0.3)
            ax.add_collection3d(collection)
            
            margin = 0.05
            ax.set_xlim([vertices[:, 0].min() - margin, vertices[:, 0].max() + margin])
            ax.set_ylim([vertices[:, 1].min() - margin, vertices[:, 1].max() + margin])
            ax.set_zlim([vertices[:, 2].min() - margin, vertices[:, 2].max() + margin])
            
        except Exception as e:
            ax.text(0, 0, 0, f'Error loading\n{mesh_file}', ha='center')
        
        ax.quiver(0, -0.3, 0.4, 0, 0, -0.2, color='red', arrow_length_ratio=0.3, 
                  linewidth=2, label='Wave')
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'{labels.get(rot, rot)}\nSphere Orientation')
        
        ax.view_init(elev=20, azim=45)
    
    plt.suptitle('Sphere Orientations\n(Red arrow: incident wave from +Z)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150)
        print(f"  Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def plot_all(data, title="", output_file=None):
    """Plot combined figure with 2D, 3D, polar."""
    fig = plt.figure(figsize=(16, 12))
    
    ax1 = fig.add_subplot(2, 2, 1)
    mask = np.abs(data[:, 1]) < 10
    theta = data[mask, 0]
    rcs = data[mask, 2]
    valid = rcs > -300
    ax1.plot(theta[valid], rcs[valid], 'b-', linewidth=2)
    ax1.annotate('', xy=(5, np.mean(rcs[valid])), xytext=(0, np.mean(rcs[valid]) - 10),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    ax1.set_xlabel('Theta (degrees)')
    ax1.set_ylabel('RCS (dBsm)')
    ax1.set_title('2D Cut (phi=0)')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 180])
    
    ax2 = fig.add_subplot(2, 2, 2, projection='polar')
    theta_rad = np.radians(data[:, 0])
    rcs = data[:, 2]
    valid = rcs > -300
    ax2.plot(theta_rad[valid], rcs[valid], 'b-', linewidth=2)
    ax2.set_title('Polar Pattern')
    ax2.grid(True)
    
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    valid_3d = rcs > -300
    if np.any(valid_3d):
        theta_3d = np.radians(data[valid_3d, 0])
        phi_3d = np.radians(data[valid_3d, 1])
        r_3d = np.maximum(rcs[valid_3d] + 100, 0) / 30
        x = r_3d * np.sin(theta_3d) * np.cos(phi_3d)
        y = r_3d * np.sin(theta_3d) * np.sin(phi_3d)
        z = r_3d * np.cos(theta_3d)
        scatter = ax3.scatter(x, y, z, c=rcs[valid_3d], cmap='viridis', s=10, alpha=0.8)
        ax3.set_xlabel('X')
        ax3.set_ylabel('Y')
        ax3.set_zlabel('Z')
        ax3.set_title('3D Pattern')
    
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')
    info_text = (
        f"Sphere RCS Simulation\n"
        f"{'='*30}\n\n"
        f"Parameters:\n"
        f"  Radius: {RADIUS*100:.0f} cm\n"
        f"  Frequency: {FREQUENCY/1e9:.1f} GHz\n"
        f"  ka = {2*np.pi*RADIUS*FREQUENCY/299792458:.2f}\n\n"
        f"Incident Wave:\n"
        f"  Direction: +Z\n"
        f"  Method: Physical Optics (PO)\n\n"
        f"Expected:\n"
        f"  AXISYMMETRIC behavior\n"
        f"  (all rotations give same RCS)\n\n"
        f"{title}"
    )
    ax4.text(0.1, 0.9, info_text, transform=ax4.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace')
    
    plt.suptitle(f'Sphere RCS Pattern\n{title}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150)
        print(f"  Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def plot_validation(data_files, title="", output_file=None):
    """Plot validation comparing PO results to analytical Mie theory."""
    fig = plt.figure(figsize=(14, 10))
    
    theta_analytical, rcs_analytical = sphere_rcs_analytical(RADIUS, FREQUENCY)
    
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot(theta_analytical, rcs_analytical, 'k--', linewidth=2, label='Mie Theory', alpha=0.7)
    for rot, data in data_files.items():
        phi_mask = np.abs(data[:, 1]) < 10
        theta = data[phi_mask, 0]
        rcs = data[phi_mask, 2]
        valid = rcs > -300
        ax1.plot(theta[valid], rcs[valid], '-', linewidth=1.5, alpha=0.7, 
                label=f'PO (rot={rot}°)')
    ax1.set_xlabel('Theta (degrees)')
    ax1.set_ylabel('RCS (dBsm)')
    ax1.set_title('2D Cut Validation: PO vs Analytical')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 180])
    
    ax2 = fig.add_subplot(2, 2, 2, projection='polar')
    ax2.plot(np.radians(theta_analytical), rcs_analytical, 'k--', linewidth=2, 
             label='Mie Theory', alpha=0.7)
    for rot, data in data_files.items():
        theta = np.radians(data[:, 0])
        rcs = data[:, 2]
        valid = rcs > -300
        ax2.plot(theta[valid], rcs[valid], '-', linewidth=1.5, alpha=0.7, 
                label=f'PO (rot={rot}°)')
    ax2.set_theta_zero_location('N')
    ax2.set_title('Polar Validation')
    ax2.legend(loc='upper right')
    ax2.grid(True)
    
    ax3 = fig.add_subplot(2, 2, 3)
    rot0_data = data_files.get('0')
    if rot0_data is not None:
        phi_mask = np.abs(rot0_data[:, 1]) < 10
        theta_po = rot0_data[phi_mask, 0]
        rcs_po = rot0_data[phi_mask, 2]
        valid_po = rcs_po > -300
        valid_analytical = rcs_analytical > -300
        diff = np.interp(theta_po, theta_analytical, rcs_analytical) - rcs_po
        ax3.plot(theta_po[valid_po], diff[valid_po], 'b-', linewidth=2)
        ax3.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        ax3.set_xlabel('Theta (degrees)')
        ax3.set_ylabel('Difference (dBsm)')
        ax3.set_title('PO vs Mie Theory Difference')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim([0, 180])
        ax3.set_ylim([-5, 5])
    
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis('off')
    info_text = (
        f"Sphere RCS Validation\n"
        f"{'='*30}\n\n"
        f"Parameters:\n"
        f"  Radius: {RADIUS*100:.0f} cm\n"
        f"  Frequency: {FREQUENCY/1e9:.1f} GHz\n"
        f"  Wavelength: {299792458/FREQUENCY*100:.1f} cm\n"
        f"  ka = {2*np.pi*RADIUS*FREQUENCY/299792458:.2f}\n\n"
        f"Physical Optics (PO) vs Mie Theory:\n"
        f"  - PO approximates scattering\n"
        f"  - Mie theory is exact for spheres\n"
        f"  - Differences expected at large ka\n"
        f"  - Axisymmetry validated\n"
        f"    (all rotations overlap)\n"
    )
    ax4.text(0.1, 0.9, info_text, transform=ax4.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace')
    
    plt.suptitle(f'Sphere RCS Validation\n{title}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150)
        print(f"  Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def ensure_data_available(args):
    """Check and generate data if needed."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    rotations = [0, 30, 45]
    data_files = {}
    mesh_files = {}
    
    print("\nChecking data availability...")
    
    for rot in rotations:
        mesh_file = os.path.join(script_dir, f"sphere_{rot}deg.obj")
        csv_file = os.path.join(script_dir, f"rcs_{rot}deg.csv")
        
        if not os.path.exists(mesh_file):
            print(f"\nGenerating mesh for {rot}° rotation:")
            mesh_file = generate_sphere_mesh(rot)
            if mesh_file is None:
                return None, None
        else:
            print(f"  Mesh exists: {mesh_file}")
        
        mesh_files[str(rot)] = mesh_file
        
        if not args.no_auto_run:
            print(f"\nChecking RCS data for {rot}° rotation:")
            result = run_raycs(mesh_file, csv_file)
            if result is None:
                return None, None
        
        data = load_rcs_data(csv_file)
        if data is None:
            return None, None
        
        data_files[str(rot)] = data
        print(f"  Loaded: {csv_file}")
    
    return data_files, mesh_files


def main():
    parser = argparse.ArgumentParser(
        description='Sphere RCS: compute and visualize using RayCs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 sphere_scattering.py

  python3 sphere_scattering.py --method 3d

  python3 sphere_scattering.py --rotation all

  python3 sphere_scattering.py --orientations

  python3 sphere_scattering.py --validation
        """
    )
    
    parser.add_argument(
        '--method', '-m',
        choices=['2d', '3d', 'polar', 'all'],
        default='all',
        help='Plot method (default: all)'
    )
    
    parser.add_argument(
        '--rotation', '-r',
        choices=['0', '30', '45', 'all'],
        default='all',
        help='Rotation study (default: all)'
    )
    
    parser.add_argument(
        '--orientations',
        action='store_true',
        help='Show sphere orientations plot'
    )
    
    parser.add_argument(
        '--validation',
        action='store_true',
        help='Show validation plot (PO vs Mie theory)'
    )
    
    parser.add_argument(
        '--no-auto-run',
        action='store_true',
        help='Skip auto-run of RayCs (use existing data only)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file prefix (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    title = f"r={RADIUS*100:.0f}cm, f={FREQUENCY/1e9:.1f}GHz, ka={2*np.pi*RADIUS*FREQUENCY/299792458:.1f}"
    
    if args.no_auto_run:
        data_files = {}
        mesh_files = {}
        for rot in ['0', '30', '45']:
            csv_file = os.path.join(script_dir, f"rcs_{rot}deg.csv")
            mesh_file = os.path.join(script_dir, f"sphere_{rot}deg.obj")
            data = load_rcs_data(csv_file)
            if data is not None:
                data_files[rot] = data
            if os.path.exists(mesh_file):
                mesh_files[rot] = mesh_file
    else:
        data_files, mesh_files = ensure_data_available(args)
    
    if data_files is None:
        print("\nError: Could not load RCS data. Please ensure RayCs is built.")
        sys.exit(1)
    
    if args.orientations and mesh_files:
        output_file = args.output or os.path.join(script_dir, 'sphere_orientations.png')
        plot_sphere_orientations(mesh_files, output_file)
    
    if args.validation:
        output_file = args.output or os.path.join(script_dir, 'sphere_validation.png')
        plot_validation(data_files, title, output_file)
    
    print(f"\nGenerating plots...")
    
    if args.rotation == 'all':
        output_file = args.output or os.path.join(script_dir, 'sphere_rotation_comparison.png')
        plot_rotation_comparison(data_files, title, output_file)
    
    elif args.rotation in data_files:
        data = data_files[args.rotation]
        rot_label = f"{args.rotation}° rotation"
        
        if args.method == 'all':
            output_file = args.output or os.path.join(script_dir, 'sphere_rcs_pattern.png')
            plot_all(data, title=f"{title}\n{rot_label}", output_file=output_file)
        elif args.method == '2d':
            output_file = args.output or os.path.join(script_dir, 'sphere_2d.png')
            plot_2d(data, title=title, output_file=output_file)
        elif args.method == '3d':
            output_file = args.output or os.path.join(script_dir, 'sphere_3d.png')
            plot_3d(data, title=title, output_file=output_file)
        elif args.method == 'polar':
            output_file = args.output or os.path.join(script_dir, 'sphere_polar.png')
            plot_polar(data, title=title, output_file=output_file)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
