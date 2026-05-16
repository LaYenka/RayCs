#!/usr/bin/env python3
"""
Plot RCS radiation pattern from RayCs output CSV.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D
import argparse
import sys

def plot_rcs_pattern(csv_file, output_file=None, method='3d'):
    """
    Plot RCS radiation pattern from CSV output.
    """
    # Read CSV data
    data = np.genfromtxt(csv_file, delimiter=',', skip_header=1)
    
    theta = data[:, 0]
    phi = data[:, 1]
    rcs_total = data[:, 2]
    rcs_vv = data[:, 3]
    rcs_hh = data[:, 4]
    
    if method == '2d':
        # Plot 2D cuts
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Theta cut at phi=0 or phi=90
        phi_0_idx = np.where(np.abs(phi - 0) < 1)[0]
        phi_90_idx = np.where(np.abs(phi - 90) < 1)[0]
        
        if len(phi_0_idx) > 0:
            axes[0].plot(theta[phi_0_idx], rcs_total[phi_0_idx], 'b-', label='Total')
            axes[0].plot(theta[phi_0_idx], rcs_vv[phi_0_idx], 'r--', label='VV')
            axes[0].plot(theta[phi_0_idx], rcs_hh[phi_0_idx], 'g--', label='HH')
            
            # Add incident wave arrow
            axes[0].annotate('', xy=(5, -10), xytext=(0, -30),
                           arrowprops=dict(arrowstyle='->', color='red', lw=2))
            axes[0].text(2.5, -35, 'Incident\nWave', ha='center', fontsize=10, color='red')
            
            axes[0].set_xlabel('Theta (degrees)')
            axes[0].set_ylabel('RCS (dBsm)')
            axes[0].set_title('RCS vs Theta (phi=0°)')
            axes[0].legend()
            axes[0].grid(True)
        
        if len(phi_90_idx) > 0:
            axes[1].plot(theta[phi_90_idx], rcs_total[phi_90_idx], 'b-', label='Total')
            axes[1].plot(theta[phi_90_idx], rcs_vv[phi_90_idx], 'r--', label='VV')
            axes[1].plot(theta[phi_90_idx], rcs_hh[phi_90_idx], 'g--', label='HH')
            axes[1].set_xlabel('Theta (degrees)')
            axes[1].set_ylabel('RCS (dBsm)')
            axes[1].set_title('RCS vs Theta (phi=90°)')
            axes[1].legend()
            axes[1].grid(True)
        
        plt.tight_layout()
        
    elif method == '3d':
        # Create 3D radiation pattern
        from mpl_toolkits.mplot3d import Axes3D
        
        # Convert to spherical coordinates for 3D plot
        theta_rad = np.radians(theta)
        phi_rad = np.radians(phi)
        
        # Convert dB to linear scale for plotting
        rcs_linear = 10**(rcs_total / 10)
        
        # Normalize for visualization
        rcs_norm = rcs_linear / np.max(rcs_linear)
        
        # Convert to Cartesian
        x = rcs_norm * np.sin(theta_rad) * np.cos(phi_rad)
        y = rcs_norm * np.sin(theta_rad) * np.sin(phi_rad)
        z = rcs_norm * np.cos(theta_rad)
        
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot scatter points
        scatter = ax.scatter(x, y, z, c=rcs_total, cmap='viridis', s=10, alpha=0.8)
        
        # Add incident wave arrow (from +Z direction toward origin)
        arrow_length = 1.5
        ax.quiver(0, 0, 2, 0, 0, -arrow_length, color='red', arrow_length_ratio=0.3, 
                  linewidth=3, label='Incident Wave')
        
        # Mark the incident direction
        ax.text(0, 0, 2.3, '+Z', fontsize=12, color='red', ha='center')
        ax.text(0, 0, -0.5, 'Incident\nWave', fontsize=10, color='red', ha='center')
        
        # Add origin marker
        ax.scatter([0], [0], [0], s=100, c='blue', marker='o', label='Object')
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('3D RCS Radiation Pattern\n(Red arrow: incident wave from +Z)')
        
        # Add colorbar
        cbar = fig.colorbar(scatter, shrink=0.5, aspect=10)
        cbar.set_label('RCS (dBsm)')
        
        # Add legend
        ax.legend(loc='upper left')
        
    elif method == 'polar':
        # Polar plot (azimuth cut)
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(10, 8))
        
        theta_rad = np.radians(theta)
        
        ax.plot(theta_rad, rcs_total, 'b-', linewidth=2, label='Total')
        ax.plot(theta_rad, rcs_vv, 'r--', linewidth=1, label='VV')
        ax.plot(theta_rad, rcs_hh, 'g--', linewidth=1, label='HH')
        
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_xlabel('RCS (dBsm)', labelpad=30)
        
        # Add incident wave arrow at theta = 0° (north = +Z direction)
        # In polar plot, theta=0 is at the top (north)
        # The incident wave comes FROM theta=0, so we show arrow at edge pointing inward
        r_max = ax.get_rmax()
        ax.annotate('', xy=(0, r_max * 0.85), xytext=(0, r_max * 1.1),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.text(0, r_max * 1.2, 'Incident\nWave', ha='center', fontsize=9, color='red')
        
        ax.set_title('RCS Polar Pattern\n(Red arrow: incident wave from +Z)', pad=20)
        ax.legend(loc='upper right')
        ax.grid(True)
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved plot to: {output_file}")
    else:
        plt.show()


def create_sample_data():
    """
    Create sample RCS data for testing.
    """
    theta = np.linspace(0, 180, 181)
    phi = np.zeros_like(theta)
    
    # Simulate sphere RCS (Mie theory - oscillates, decays)
    # For a PEC sphere: RCS = pi * r^2 * (ka)^2 for large ka
    r = 1.0  # radius in wavelengths
    ka = 2 * np.pi * r
    
    # Approximate sphere RCS (oscillations + average)
    rcs_avg = 10 * np.log10(np.pi * r**2)  # ~5 dBsm for r=1 wavelength
    rcs = rcs_avg + 3 * np.sin(2 * ka * np.sin(np.radians(theta))**2 * np.exp(-0.1*theta))
    
    # Write to CSV
    with open('rcs_sample.csv', 'w') as f:
        f.write('theta_deg,phi_deg,RCS_total_dBsm,RCS_VV_dBsm,RCS_HH_dBsm\n')
        for i in range(len(theta)):
            f.write(f"{theta[i]},{phi[i]},{rcs[i]:.2f},{rcs[i]:.2f},{rcs[i]:.2f}\n")
    
    print("Created sample data: rcs_sample.csv")
    return 'rcs_sample.csv'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot RCS radiation pattern')
    parser.add_argument('csv_file', nargs='?', help='Input CSV file')
    parser.add_argument('--method', choices=['2d', '3d', 'polar'], default='3d',
                        help='Plotting method')
    parser.add_argument('-o', '--output', help='Output image file')
    
    args = parser.parse_args()
    
    if args.csv_file:
        try:
            plot_rcs_pattern(args.csv_file, args.output, args.method)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Create sample data for demonstration
        sample_file = create_sample_data()
        plot_rcs_pattern(sample_file, args.output or 'rcs_pattern.png', args.method)
