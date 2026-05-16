#!/usr/bin/env python3
"""
Convert OBJ mesh to CGNS format for RayCs.
Creates a CGNS/Python-friendly HDF5 file.
"""

import numpy as np
import h5py
import sys
import os
import struct

def obj_to_cgns(obj_file, cgns_file, scale=1.0):
    """Convert OBJ mesh to CGNS HDF5 file."""
    
    vertices = []
    faces = []
    
    with open(obj_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('v '):
                parts = line.split()
                x = float(parts[1]) * scale
                y = float(parts[2]) * scale
                z = float(parts[3]) * scale
                vertices.append((x, y, z))
            elif line.startswith('f '):
                parts = line.split()
                indices = []
                for p in parts[1:]:
                    idx = int(p.split('/')[0]) - 1
                    indices.append(idx)
                if len(indices) == 3:
                    faces.append(indices)
                elif len(indices) == 4:
                    faces.append([indices[0], indices[1], indices[2]])
                    faces.append([indices[0], indices[2], indices[3]])
    
    n_verts = len(vertices)
    n_faces = len(faces)
    
    print(f"Loaded: {n_verts} vertices, {n_faces} triangles")
    
    x = np.array([v[0] for v in vertices], dtype=np.float64)
    y = np.array([v[1] for v in vertices], dtype=np.float64)
    z = np.array([v[2] for v in vertices], dtype=np.float64)
    
    conn = np.array(faces, dtype=np.int32).flatten() + 1
    
    with h5py.File(cgns_file, 'w') as f:
        f.create_dataset('coords/x', data=x)
        f.create_dataset('coords/y', data=y)
        f.create_dataset('coords/z', data=z)
        f.create_dataset('connectivity/triangles', data=conn)
        f.attrs['nverts'] = n_verts
        f.attrs['nelems'] = n_faces
    
    print(f"Created: {cgns_file}")


if __name__ == '__main__':
    obj_file = 'sphere.obj'
    cgns_file = 'sphere.cgns'
    
    if len(sys.argv) > 1:
        obj_file = sys.argv[1]
    if len(sys.argv) > 2:
        cgns_file = sys.argv[2]
    
    if not os.path.exists(obj_file):
        print(f"Error: {obj_file} not found")
        sys.exit(1)
    
    obj_to_cgns(obj_file, cgns_file)
