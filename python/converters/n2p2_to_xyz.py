#!/usr/bin/python
"""
Converts an N2P2/Runner formatted data file into extended XYZ format.

Usage: 
    n2p2_to_xyz.py < input.data > output.xyz
"""

import sys

def process_structure(lines):
    # Extracting lattice vectors, atoms, energy, and charge
    lattice_vectors = []
    atoms = []
    energy = charge = 0.0
    for line in lines:
        if line.startswith("lattice"):
            lattice_vectors.append(line.split()[1:])
        elif line.startswith("atom"):
            atoms.append(line.split()[1:])
        elif line.startswith("energy"):
            energy = line.split()[1]
        elif line.startswith("charge"):
            charge = line.split()[1]

    # Constructing the lattice string for XYZ format
    lattice_str = " ".join([" ".join(v) for v in lattice_vectors])

    # Preparing the XYZ format
    xyz_lines = []
    xyz_lines.append(f'{len(atoms)}')
    xyz_lines.append(f'Lattice="{lattice_str}" Properties=species:S:1:pos:R:3:forces:R:3 energy="{energy}" charge="{charge}"')
    
    for atom in atoms:
        # Atom format: [symbol, x, y, z, fx, fy, fz]
        xyz_lines.append(f'{atom[3]} {" ".join(atom[:3])} {" ".join(atom[6:])}')

    return "\n".join(xyz_lines)

def main():
    input_lines = sys.stdin.readlines()
    structures = []
    current_structure = []
    for line in input_lines:
        line = line.strip()
        if line == "begin":
            current_structure = []
        elif line == "end":
            structures.append(process_structure(current_structure))
        else:
            current_structure.append(line)

    # Print the processed structures in XYZ format
    for structure in structures:
        print(structure)

if __name__ == "__main__":
    main()

