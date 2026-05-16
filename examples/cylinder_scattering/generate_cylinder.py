#!/usr/bin/env python3
"""
Generate cylinder mesh for RayCs scattering simulation.
"""

import numpy as np
import sys


def rotate_around_x(vertices, angle_deg):
    """Rotate vertices around X axis."""
    angle = np.radians(angle_deg)
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    rotated = []
    for v in vertices:
        x, y, z = v
        y_new = y * cos_a - z * sin_a
        z_new = y * sin_a + z * cos_a
        rotated.append((x, y_new, z_new))
    return rotated


def generate_cylinder_mesh(radius=0.1, length=0.5, n_circ=40, n_length=20, output_file='cylinder.obj', rotation_deg=0):
    """
    Generate cylinder mesh in OBJ format.
    
    Parameters:
    - radius: cylinder radius (m)
    - length: cylinder length (m)
    - n_circ: number of divisions around circumference
    - n_length: number of divisions along length
    - output_file: output filename
    - rotation_deg: rotation around X axis in degrees
    """
    
    vertices = []
    faces = []
    
    # Generate vertices for cylinder sides
    for i in range(n_length + 1):
        z = -length/2 + length * i / n_length
        for j in range(n_circ):
            phi = 2 * np.pi * j / n_circ
            x = radius * np.cos(phi)
            y = radius * np.sin(phi)
            vertices.append((x, y, z))
    
    # Generate side faces (quads as two triangles)
    for i in range(n_length):
        for j in range(n_circ):
            p0 = i * n_circ + j
            p1 = i * n_circ + (j + 1) % n_circ
            p2 = (i + 1) * n_circ + (j + 1) % n_circ
            p3 = (i + 1) * n_circ + j
            faces.append((p0+1, p1+1, p2+1))
            faces.append((p0+1, p2+1, p3+1))
    
    # Add end caps (flat circular caps)
    # Indices (0-indexed):
    # side vertices: 0 to (n_length+1)*n_circ-1
    # top ring: (n_length+1)*n_circ to (n_length+2)*n_circ-1  [840-880]
    # center_top: (n_length+2)*n_circ  [881]
    # bottom ring: (n_length+2)*n_circ+1 to (n_length+3)*n_circ  [882-921]
    # center_bottom: (n_length+3)*n_circ+1  [922]
    
    side_vertex_count = (n_length + 1) * n_circ  # 840
    
    # Top cap ring vertices first
    for j in range(n_circ):
        phi = 2 * np.pi * j / n_circ
        x = radius * np.cos(phi)
        y = radius * np.sin(phi)
        vertices.append((x, y, length/2))
    
    center_top = len(vertices)  # = 840 + 40 = 880
    vertices.append((0, 0, length/2))  # center at 880
    
    # Bottom cap ring vertices
    for j in range(n_circ):
        phi = 2 * np.pi * j / n_circ
        x = radius * np.cos(phi)
        y = radius * np.sin(phi)
        vertices.append((x, y, -length/2))
    
    center_bottom = len(vertices)  # = 880 + 40 + 1 = 921
    vertices.append((0, 0, -length/2))  # center at 921
    
    top_first = side_vertex_count  # = 840, first top ring vertex
    bottom_first = center_top + 1  # = 881, first bottom ring vertex
    
    # Add top cap faces (fan from center, outward normal = +Z)
    for j in range(n_circ):
        p0 = center_top + 1  # center vertex (1-indexed)
        p1 = top_first + j + 1  # current ring vertex (1-indexed)
        p2 = top_first + (j + 1) % n_circ + 1  # next ring vertex (1-indexed)
        faces.append((p0, p1, p2))  # CCW from +Z direction
    
    # Add bottom cap faces (fan from center, outward normal = -Z)
    for j in range(n_circ):
        p0 = center_bottom + 1  # center vertex (1-indexed)
        p1 = bottom_first + j + 1  # current ring vertex (1-indexed)
        p2 = bottom_first + (j + 1) % n_circ + 1  # next ring vertex (1-indexed)
        faces.append((p0, p2, p1))  # CW from +Z gives outward -Z normal
    
    # Apply rotation if specified
    if rotation_deg != 0:
        vertices = rotate_around_x(vertices, rotation_deg)
    
    # Write OBJ file
    with open(output_file, 'w') as f:
        f.write(f"# Cylinder: r={radius}m, L={length}m, rot={rotation_deg}deg\n")
        
        for v in vertices:
            f.write(f"v {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n")
        
        for face in faces:
            f.write(f"f {face[0]} {face[1]} {face[2]}\n")
    
    print(f"Created: {output_file} ({len(faces)} triangles)")
    
    return output_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate cylinder mesh')
    parser.add_argument('--radius', type=float, default=0.1, help='Cylinder radius (m)')
    parser.add_argument('--length', type=float, default=0.5, help='Cylinder length (m)')
    parser.add_argument('--n-circ', type=int, default=40, help='Circumference divisions')
    parser.add_argument('--n-length', type=int, default=20, help='Length divisions')
    parser.add_argument('--rotation', type=float, default=0, help='Rotation around X axis (deg)')
    parser.add_argument('--output', type=str, default='cylinder.obj', help='Output file')
    
    args = parser.parse_args()
    
    generate_cylinder_mesh(args.radius, args.length, args.n_circ, args.n_length, args.output, args.rotation)


if __name__ == "__main__":
    main()