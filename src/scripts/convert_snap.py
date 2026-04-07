"""
convert_snap.py
Converts a SNAP edge-list (.txt) to the project's LIST format.
Remaps non-contiguous node IDs to 0-indexed, assigns synthetic integer weights.

Usage:
    python convert_snap.py <input.txt> <output.txt> [source] [--seed N] [--min-w N] [--max-w N]

Examples:
    python convert_snap.py p2p-Gnutella04.txt test/real_world/p2p-gnutella.txt 0
    python convert_snap.py roadNet-CA.txt test/real_world/road-CA.txt 0 --seed 99 --min-w 1 --max-w 50

Notes:
    - SNAP files use tab-separated edges with comment lines starting with '#'.
    - Node IDs in SNAP are not always contiguous; this script remaps them to [0, N-1].
    - Weights are assigned randomly (uniform integer) since SNAP graphs are unweighted.
      Use a fixed --seed for reproducibility across runs.
    - Download datasets from: https://snap.stanford.edu/data/
      Recommended: p2p-Gnutella04.txt.gz, roadNet-CA.txt.gz
"""

import sys
import os
import random
import argparse


def convert(input_path: str, output_path: str, source_original: int = None,
            seed: int = 42, min_w: int = 1, max_w: int = 100) -> None:
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    raw_edges = []
    nodes = set()

    with open(input_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            u, v = int(parts[0]), int(parts[1])
            if u == v:
                continue  # skip self-loops
            raw_edges.append((u, v))
            nodes.update([u, v])

    # remap node IDs to contiguous 0-indexed range
    id_map = {n: i for i, n in enumerate(sorted(nodes))}
    n_vertices = len(nodes)

    # assign synthetic weights reproducibly
    rng = random.Random(seed)
    edges = [(id_map[u], id_map[v], rng.randint(min_w, max_w)) for u, v in raw_edges]

    # resolve source: default to 0 in remapped space
    if source_original is not None:
        if source_original not in id_map:
            print(f"Error: source node {source_original} not found in graph")
            sys.exit(1)
        source = id_map[source_original]
    else:
        source = 0

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
    print(f"  Source   : {source} (remapped from {source_original if source_original is not None else 'default'})")
    print(f"  Weights  : uniform integer [{min_w}, {max_w}], seed={seed}")
    print(f"  Output   : {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert SNAP edge list to project LIST format.")
    parser.add_argument("input",  help="Path to SNAP .txt edge list")
    parser.add_argument("output", help="Path to write converted output")
    parser.add_argument("source", nargs="?", type=int, default=None,
                        help="Source node ID (original SNAP ID, default: maps to 0)")
    parser.add_argument("--seed",  type=int, default=42,  help="RNG seed for weight assignment (default: 42)")
    parser.add_argument("--min-w", type=int, default=1,   help="Minimum synthetic edge weight (default: 1)")
    parser.add_argument("--max-w", type=int, default=100, help="Maximum synthetic edge weight (default: 100)")
    args = parser.parse_args()

    convert(args.input, args.output, args.source, args.seed, args.min_w, args.max_w)
