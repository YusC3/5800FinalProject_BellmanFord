# ──────────────────────────────────────────────
# Bellman-Ford-Moore algorithm
# ──────────────────────────────────────────────

from graph import AdjacencyListGraph, AdjacencyMatrixGraph
from typing import Union
import math
import time
import logging

# Shared logger — configured and owned by run_single_test_case.py.
# Using a named logger means both modules share the exact same instance
# without passing any objects around.
logger = logging.getLogger("bfm")

# Module-level dict populated after every bellman_ford_moore() call.
# run_single_test_case.py reads this immediately after each call to include
# performance metrics in the log — no extra return values needed.
last_run: dict = {
    "rounds":      0,
    "relaxations": 0,
    "early_stop":  False,
    "elapsed_sec": 0.0,
}


def bellman_ford_moore(
    graph: Union[AdjacencyListGraph, AdjacencyMatrixGraph],
    source: int,
) -> tuple[list[float], list[int | None]]:
    """
    Bellman-Ford-Moore single-source shortest-path algorithm.

    Works on directed graphs with positive or negative edge weights.
    Detects negative-weight cycles reachable from the source.

    Parameters
    ----------
    graph  : AdjacencyListGraph or AdjacencyMatrixGraph
    source : index of the source vertex

    Returns
    -------
    dist  : dist[v]  = shortest distance from source to v
            (math.inf if unreachable, -math.inf if on/reachable from a
             negative cycle)
    prev  : prev[v]  = predecessor of v on the shortest path, or None

    Raises
    ------
    ValueError if source is out of range.

    Side Effects
    ------------
    Populates the module-level `last_run` dict with performance metrics
    after each call so run_single_test_case.py can log them cleanly:
      - rounds      : outer loop iterations completed
      - relaxations : total dist[v] updates performed
      - early_stop  : True if Moore's optimisation triggered early exit
      - elapsed_sec : wall-clock time covering Steps 2 and 3 only
    """
    V = graph.V
    if not (0 <= source < V):
        raise ValueError(f"Source {source} is out of range [0, {V - 1}]")

    # Step 1 – initialise distances
    dist: list[float] = [math.inf] * V
    prev: list[int | None] = [None] * V
    dist[source] = 0.0

    # ── performance counters ──────────────────────────────────────────────────
    total_rounds      = 0
    total_relaxations = 0
    early_stop        = False

    # ── start timing (Steps 2 + 3 only — no I/O or graph construction) ────────
    t_start = time.perf_counter()

    # Step 2 – relax all edges V-1 times
    for _ in range(V - 1):
        total_rounds += 1
        round_relaxations = 0
        updated = False

        for u, v, w in graph.iter_edges():
            if dist[u] != math.inf and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                round_relaxations += 1
                updated = True

        total_relaxations += round_relaxations

        # Early exit — Moore's optimisation
        if not updated:
            early_stop = True
            break

    # Step 3 – detect negative-weight cycles
    for _ in range(V):
        for u, v, w in graph.iter_edges():
            if dist[u] != math.inf and dist[u] + w < dist[v]:
                dist[v] = -math.inf
                prev[v] = u

    # ── stop timing ───────────────────────────────────────────────────────────
    elapsed_sec = time.perf_counter() - t_start

    # Populate module-level last_run so run_single_test_case.py can read
    # performance metrics without needing an extra return value.
    import bellman_ford_algorithm as _self
    _self.last_run["rounds"]      = total_rounds
    _self.last_run["relaxations"] = total_relaxations
    _self.last_run["early_stop"]  = early_stop
    _self.last_run["elapsed_sec"] = elapsed_sec

    return dist, prev


# ──────────────────────────────────────────────
# Path reconstruction helper
# ──────────────────────────────────────────────

def reconstruct_path(
    prev: list[int | None],
    source: int,
    target: int,
) -> list[int] | None:
    """
    Reconstruct the shortest path from source to target using the
    predecessor array returned by bellman_ford_moore.

    Returns a list of vertex indices [source, ..., target],
    or None if target is unreachable.
    """
    if prev[target] is None and target != source:
        return None  # unreachable

    path = []
    current: int | None = target
    visited = set()

    while current is not None:
        if current in visited:
            return None  # cycle detected in predecessor chain
        visited.add(current)
        path.append(current)
        if current == source:
            break
        current = prev[current]
    else:
        return None  # didn't reach source

    path.reverse()
    return path


# ──────────────────────────────────────────────
# Pretty-print results
# ──────────────────────────────────────────────

def print_results(
    dist: list[float],
    prev: list[int | None],
    source: int,
) -> None:
    print(f"\n{'Vertex':<10} {'Distance from source':<25} {'Path'}")
    print("-" * 60)
    for v in range(len(dist)):
        d = dist[v]
        if d == math.inf:
            dist_str = "∞  (unreachable)"
            path_str = "—"
        elif d == -math.inf:
            dist_str = "-∞  (negative cycle)"
            path_str = "⚠ affected by negative cycle"
        else:
            dist_str = str(d)
            path = reconstruct_path(prev, source, v)
            path_str = " → ".join(map(str, path)) if path else "—"
        print(f"{v:<10} {dist_str:<25} {path_str}")