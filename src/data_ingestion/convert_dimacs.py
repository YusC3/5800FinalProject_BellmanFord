"""
convert_dimacs.py
Converts a DIMACS 9th Challenge .gr file to the project's LIST format.

Usage:
    python convert_dimacs.py <input.gr> <output.txt> [source]

Example:
    python convert_dimacs.py USA-road-t.NY.gr test/real_world/road-NY.txt 0

Notes:
    - DIMACS node IDs are 1-indexed; output is converted to 0-indexed.
    - Edge weights are travel times (integers, unit: hundreds of seconds).
    - Download .gr files from:
        http://www.diag.uniroma1.it/challenge9/data/USA-road-t/
      e.g. USA-road-t.NY.gr.gz, USA-road-t.BAY.gr.gz, USA-road-t.COL.gr.gz
"""

import sys
import os


def convert(input_path: str, output_path: str, source: int = 0) -> None:
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    edges = []
    n_vertices = 0
    n_edges_expected = 0

    with open(input_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("c"):
                continue
            elif line.startswith("p"):
                # p sp <nodes> <edges>
                parts = line.split()
                n_vertices = int(parts[2])
                n_edges_expected = int(parts[3])
            elif line.startswith("a"):
                # a <src> <dst> <weight>  (1-indexed)
                parts = line.split()
                u = int(parts[1]) - 1  # convert to 0-indexed
                v = int(parts[2]) - 1
                w = int(parts[3])
                edges.append((u, v, w))

    if source < 0 or source >= n_vertices:
        print(f"Error: source {source} out of range [0, {n_vertices - 1}]")
        sys.exit(1)

    if len(edges) != n_edges_expected:
        print(f"Warning: expected {n_edges_expected} edges, parsed {len(edges)}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True) if os.path.dirname(output_path) else None

    with open(output_path, "w") as f:
        f.write(f"LIST\n")
        f.write(f"{n_vertices}\n")
        f.write(f"{len(edges)}\n")
        for u, v, w in edges:
            f.write(f"{u} {v} {w}\n")
        f.write(f"{source}\n")

    print(f"Converted: {input_path}")
    print(f"  Vertices : {n_vertices}")
    print(f"  Edges    : {len(edges)}")
    print(f"  Source   : {source}")
    print(f"  Output   : {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_dimacs.py <input.gr> <output.txt> [source]")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2]
    src = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    convert(in_path, out_path, src)
