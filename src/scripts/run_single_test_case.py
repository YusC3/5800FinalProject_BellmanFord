# ──────────────────────────────────────────────
# batch_runner.py
# ──────────────────────────────────────────────
"""
Reads one or more Bellman-Ford-Moore test cases from a plain-text file,
runs the algorithm on each, and writes the results to an output file
inside a 'results/' folder.

Output naming:  results/<input_stem>_results.txt
                e.g. hard_test_cases.txt -> results/hard_test_cases_results.txt

Input file format (blank line separates test cases)
────────────────────────────────────────────────────
LIST|MATRIX          <- graph representation (case-insensitive)
<V>                  <- number of vertices
<E>                  <- number of edges
<u> <v> <weight>     <- repeated E times (int or float weight)
[<source>]           <- optional source vertex, defaults to 0
                     <- blank line (or EOF) ends the test case
"""

import io
from datetime import datetime
from pathlib import Path

from bellman_ford_algorithm import bellman_ford_moore
from graph import AdjacencyListGraph, AdjacencyMatrixGraph


# ── helpers ───────────────────────────────────────────────────────────────────

def _parse_test_cases(lines: list[str]) -> list[dict]:
    """
    Split raw lines into individual test-case dicts.
    A blank line (or EOF) signals the end of a test case.
    """
    test_cases = []
    current: list[str] = []

    def _flush(block: list[str]):
        if not block:
            return

        it = iter(block)

        rep = next(it).strip().upper()
        if rep not in ("LIST", "MATRIX"):
            raise ValueError(f"Unknown representation '{rep}'. Expected LIST or MATRIX.")
        GraphClass = AdjacencyListGraph if rep == "LIST" else AdjacencyMatrixGraph

        try:
            V = int(next(it).strip())
            E = int(next(it).strip())
        except (StopIteration, ValueError) as exc:
            raise ValueError("Could not parse V or E.") from exc

        if V < 1:
            raise ValueError(f"V must be >= 1, got {V}.")
        if E < 0:
            raise ValueError(f"E must be >= 0, got {E}.")

        edges: list[tuple] = []
        for i in range(E):
            try:
                raw = next(it).strip().split()
            except StopIteration:
                raise ValueError(
                    f"Unexpected end of file — declared E={E} but only "
                    f"{i} edge(s) found. Check the edge count in your input."
                )
            if len(raw) != 3:
                raise ValueError(
                    f"Edge #{i + 1}: expected 'u v weight' (3 values) "
                    f"but got {len(raw)} value(s): '{' '.join(raw)}'. "
                    f"Declared E={E} may not match actual edge count."
                )
            try:
                u, v, w = int(raw[0]), int(raw[1]), float(raw[2])
            except ValueError:
                raise ValueError(
                    f"Edge #{i + 1}: could not parse '{' '.join(raw)}' as "
                    f"integers/float. Declared E={E} may not match actual edge count."
                )
            if u == v:
                raise ValueError(
                    f"Edge #{i + 1}: self-loop detected (u={u}, v={v}). "
                    f"Bellman-Ford does not support self-loops."
                )
            edges.append((u, v, w))

        source = 0
        try:
            source_line = next(it).strip()
            if source_line:
                source = int(source_line)
        except StopIteration:
            pass

        if not (0 <= source < V):
            raise ValueError(f"Source vertex {source} is out of range [0, {V - 1}].")

        test_cases.append(
            dict(GraphClass=GraphClass, rep=rep, V=V, edges=edges, source=source)
        )

    for line in lines:
        stripped = line.strip()
        if stripped == "":
            _flush(current)
            current = []
        elif stripped.startswith("#"):
            continue
        else:
            current.append(line)

    _flush(current)
    return test_cases


def _format_path(prev: list, source: int, target: int) -> str:
    path = []
    node = target
    visited = set()

    while node is not None:
        if node in visited:
            return "<cycle detected>"
        visited.add(node)
        path.append(str(node))
        node = prev[node]

    if not path or int(path[-1]) != source:
        return "<unreachable>"

    return " → ".join(reversed(path))


def _format_results(dist: list, prev: list, source: int, case_num: int,
                    rep: str, V: int, edges: list) -> str:
    out = io.StringIO()

    out.write(f"{'=' * 60}\n")
    out.write(f"  Test Case #{case_num}\n")
    out.write(f"  Representation : {rep}\n")
    out.write(f"  Vertices       : {V}\n")
    out.write(f"  Edges          : {len(edges)}\n")
    out.write(f"  Source         : {source}\n")
    out.write(f"{'=' * 60}\n\n")

    if dist is None:
        out.write("  *** Negative-weight cycle detected — no solution. ***\n\n")
        return out.getvalue()

    col_w = 10
    out.write(f"  {'Vertex':<{col_w}} {'Distance':<{col_w}} {'Path from source'}\n")
    out.write(f"  {'-' * 50}\n")

    for v in range(V):
        if dist[v] == float("inf"):
            dist_str, path_str = "∞", "<unreachable>"
        else:
            dist_str = str(dist[v])
            path_str = _format_path(prev, source, v)
        out.write(f"  {v:<{col_w}} {dist_str:<{col_w}} {path_str}\n")

    out.write("\n")
    return out.getvalue()


# ── public API ────────────────────────────────────────────────────────────────

def run_batch(input_path: str | Path, output_path: str | Path) -> Path:
    """
    Read test cases from *input_path*, run Bellman-Ford-Moore on each,
    and write results to *output_path*.

    The parent directory of output_path is created if it does not exist.

    Returns the output Path.

    Raises
    ------
    FileNotFoundError : if *input_path* does not exist.
    ValueError        : if a test case is malformed.
    """
    input_path  = Path(input_path).resolve()
    output_path = Path(output_path).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = input_path.read_text(encoding="utf-8").splitlines()
    test_cases = _parse_test_cases(lines)

    if not test_cases:
        raise ValueError("No test cases found in the input file.")

    with output_path.open("w", encoding="utf-8") as fout:
        # ── timestamp header ──────────────────────────────────
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fout.write(f"Bellman-Ford-Moore — Batch Results\n")
        fout.write(f"Generated  : {stamp}\n")
        fout.write(f"Input file : {input_path}\n")
        fout.write(f"Test cases : {len(test_cases)}\n\n")

        for i, tc in enumerate(test_cases, start=1):
            graph = tc["GraphClass"](tc["V"])
            for u, v, w in tc["edges"]:
                graph.add_edge(u, v, w)

            dist, prev = bellman_ford_moore(graph, tc["source"])

            block = _format_results(
                dist, prev, tc["source"],
                case_num=i, rep=tc["rep"], V=tc["V"], edges=tc["edges"],
            )
            fout.write(block)

    return output_path


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python batch_runner.py <input_file> <output_file>")
        sys.exit(1)

    try:
        out = run_batch(sys.argv[1], sys.argv[2])
        print(f"Done — results written to '{out}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)