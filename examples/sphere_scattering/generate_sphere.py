#!/usr/bin/env python3
"""
Generate sphere mesh for RayCs.
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


def generate_sphere_mesh(radius=0.1, n_theta=20, n_phi=20, output_file='sphere.obj', rotation_deg=0):
    """Generate sphere mesh in OBJ format."""
    
    vertices = []
    faces = []
    
    # Generate sphere points
    for i in range(n_theta + 1):
        theta = np.pi * i / n_theta
        for j in range(n_phi):
            phi = 2 * np.pi * j / n_phi
            x = radius * np.sin(theta) * np.cos(phi)
            y = radius * np.sin(theta) * np.sin(phi)
            z = radius * np.cos(theta)
            vertices.append((x, y, z))
    
    # Generate triangles
    for i in range(n_theta):
        for j in range(n_phi):
            i_next = i + 1
            j_next = (j + 1) % n_phi
            
            p0 = i * n_phi + j
            p1 = i * n_phi + j_next
            p2 = i_next * n_phi + j_next
            p3 = i_next * n_phi + j
            
            if i == 0:
                faces.append((p0 + 1, p2 + 1, p3 + 1))
            elif i == n_theta - 1:
                faces.append((p0 + 1, p1 + 1, p2 + 1))
            else:
                faces.append((p0 + 1, p1 + 1, p2 + 1))
                faces.append((p0 + 1, p2 + 1, p3 + 1))
    
    if rotation_deg != 0:
        vertices = rotate_around_x(vertices, rotation_deg)
    
    with open(output_file, 'w') as f:
        f.write(f"# Sphere: r={radius}m, rot={rotation_deg}deg\n")
        for v in vertices:
            f.write(f"v {v[0]:.8f} {v[1]:.8f} {v[2]:.8f}\n")
        for face in faces:
            f.write(f"f {face[0]} {face[1]} {face[2]}\n")
    
    print(f"Created: {output_file} ({len(faces)} triangles)")
    return output_file


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate sphere mesh')
    parser.add_argument('--radius', type=float, default=0.1)
    parser.add_argument('--n-theta', type=int, default=36)
    parser.add_argument('--n-phi', type=int, default=36)
    parser.add_argument('--rotation', type=float, default=0)
    parser.add_argument('--output', type=str, default='sphere.obj')
    args = parser.parse_args()
    generate_sphere_mesh(args.radius, args.n_theta, args.n_phi, args.output, args.rotation)