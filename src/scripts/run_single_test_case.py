# ──────────────────────────────────────────────
# run_single_test_case.py  (formerly batch_runner.py)
# ──────────────────────────────────────────────
"""
Reads one or more Bellman-Ford-Moore test cases from a plain-text file,
runs the algorithm on each, and writes a structured log to an output .log file.

The "bfm" logger is initialised here and shared — bellman_ford_moore_algorithm.py
writes performance metrics into the same file via logging.getLogger("bfm").

Log structure per run
─────────────────────
  File header  : timestamp, input path, test case count, shared I/O overhead
  Per test case: Graph Details, Performance, Performance Overhead

Output naming:  results/<input_stem>_results.log
                e.g. hard_test_cases.txt -> results/hard_test_cases_results.log

Input file format (blank line separates test cases)
────────────────────────────────────────────────────
LIST|MATRIX          <- graph representation (case-insensitive)
<V>                  <- number of vertices
<E>                  <- number of edges
<u> <v> <weight>     <- repeated E times (int or float weight)
[<source>]           <- optional source vertex, defaults to 0
                     <- blank line (or EOF) ends the test case
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from bellman_ford_moore_algorithm import bellman_ford_moore
from graph import AdjacencyListGraph, AdjacencyMatrixGraph


# ── Logger setup ──────────────────────────────────────────────────────────────

def _setup_logger(log_path: Path) -> logging.Logger:
    """
    Configure the singleton "bfm" logger to write to *log_path*.
    Called once per input file. Any previous handlers are removed first
    so that re-running in the same process doesn't double-log.
    """
    logger = logging.getLogger("bfm")
    logger.setLevel(logging.DEBUG)

    # Remove stale handlers from a previous run in the same process
    logger.handlers.clear()

    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


# ── Parsing ───────────────────────────────────────────────────────────────────

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
            dict(GraphClass=GraphClass, rep=rep, V=V, E=E, edges=edges, source=source)
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


# ── Result formatting ─────────────────────────────────────────────────────────

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


def _log_results(logger: logging.Logger, dist: list, prev: list,
                 source: int, case_num: int, rep: str, V: int, edges: list,
                 perf: dict, graph_build_sec: float) -> None:
    """Log graph details, performance metrics, overhead, and correctness results."""

    logger.info("=" * 60)
    logger.info("TEST CASE #%d", case_num)
    logger.info("=" * 60)
    logger.info("")

    # ── Graph Details ─────────────────────────────────────────────────────────
    logger.info("  Graph Details")
    logger.info("  %-18s : %s",   "Representation", rep)
    logger.info("  %-18s : %d",   "Vertices",       V)
    logger.info("  %-18s : %d",   "Edges",          len(edges))
    logger.info("  %-18s : %d",   "Source",         source)
    logger.info("")

    # ── Performance ───────────────────────────────────────────────────────────
    logger.info("  Performance")
    logger.info("  %-22s : %d",     "enqueue_count",     perf["enqueue_count"])
    logger.info("  %-22s : %d",     "total_relaxations", perf["total_relaxations"])
    logger.info("  %-22s : %.2f",   "enqueue_ratio",     perf["enqueue_count"] / V)
    logger.info("  %-22s : %d",     "max_enqueues",      max(perf["enqueues_per_node"]))
    logger.info("  %-22s : %.6f s", "elapsed_sec",       perf["elapsed_sec"])
    logger.info("")

    # ── Performance Overhead ──────────────────────────────────────────────────
    logger.info("  Performance Overhead")
    logger.info("  %-18s : %.6f s", "graph_build_sec", graph_build_sec)
    logger.info("")

    # ── Correctness Results ───────────────────────────────────────────────────
    if dist is None:
        logger.info("  *** Negative-weight cycle detected — no solution. ***")
        logger.info("")
        return

    logger.info("  %-10s %-15s %s", "Vertex", "Distance", "Path from source")
    logger.info("  " + "-" * 50)

    for v in range(V):
        if dist[v] == float("inf"):
            dist_str, path_str = "inf", "<unreachable>"
        else:
            dist_str = str(dist[v])
            path_str = _format_path(prev, source, v)
        logger.info("  %-10d %-15s %s", v, dist_str, path_str)

    logger.info("")


# ── Public API ────────────────────────────────────────────────────────────────

def run_batch(input_path: str | Path, output_path: str | Path) -> Path:
    """
    Read test cases from *input_path*, run Bellman-Ford-Moore on each,
    and write a structured log (correctness + performance) to *output_path*.

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

    # ── Initialise the singleton logger for this input file ───────────────────
    logger = _setup_logger(output_path)

    # ── Read input file and time it ───────────────────────────────────────────
    t_read_start = time.perf_counter()
    lines = input_path.read_text(encoding="utf-8").splitlines()
    io_read_sec = time.perf_counter() - t_read_start

    test_cases = _parse_test_cases(lines)

    if not test_cases:
        raise ValueError("No test cases found in the input file.")

    # ── File header ───────────────────────────────────────────────────────────
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("Bellman-Ford-Moore — Batch Results")
    logger.info("Generated   : %s", stamp)
    logger.info("Input file  : %s", input_path)
    logger.info("Test cases  : %d", len(test_cases))
    logger.info("")
    logger.info("  I/O Overhead (shared across all test cases)")
    logger.info("  %-18s : %.6f s", "io_read_sec", io_read_sec)
    logger.info("")

    # ── Run each test case ────────────────────────────────────────────────────
    for i, tc in enumerate(test_cases, start=1):

        # Time graph construction only (not BFM)
        t_build_start = time.perf_counter()
        graph = tc["GraphClass"](tc["V"])
        for u, v, w in tc["edges"]:
            graph.add_edge(u, v, w)
        # DEBUG PRINT - Verifies no negative weights
        # neg = [(u, v, w) for u, v, w in graph.iter_edges() if w < 0]
        # if neg:
        #     print(f"WARNING: {len(neg)} negative edges — first 5: {neg[:5]}")
        # else:
        #     print("No negative weights found.")
            
        graph_build_sec = time.perf_counter() - t_build_start
        # DEBUG PRINT - verifies min weight
        # min_w = min(w for _, _, w in graph.iter_edges())
        # print(f"Min edge weight: {min_w}")

        # Run BFM — performance metrics stored in bellman_ford_algorithm.last_run
        from bellman_ford_moore_algorithm import last_run
        dist, prev = bellman_ford_moore(graph, tc["source"])

        # Log all sections for this test case
        _log_results(logger, dist, prev, tc["source"],
                     case_num=i, rep=tc["rep"], V=tc["V"], edges=tc["edges"],
                     perf=last_run, graph_build_sec=graph_build_sec)

    # Flush and close the file handler cleanly
    for handler in logger.handlers:
        handler.flush()
        handler.close()

    return output_path


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python run_single_test_case.py <input_file> <output_file>")
        sys.exit(1)

    try:
        out = run_batch(sys.argv[1], sys.argv[2])
        print(f"Done — log written to '{out}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)