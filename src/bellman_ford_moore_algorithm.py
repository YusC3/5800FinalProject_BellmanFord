# ──────────────────────────────────────────────
# Bellman-Ford-Moore algorithm
# ──────────────────────────────────────────────
from collections import deque
from graph import AdjacencyListGraph, AdjacencyMatrixGraph
from typing import Union
import math
import time
import logging

# Shared logger — configured and owned by run_single_test_case.py.
logger = logging.getLogger("bfm")

# Module-level dict populated after every bellman_ford_moore() call.
last_run: dict = {
    "enqueue_count":     0,
    "enqueues_per_node": [],
    "total_relaxations": 0,
    "early_stop":        False,
    "elapsed_sec":       0.0,
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
    Populates the module-level `last_run` dict with performance metrics:
      - enqueue_count     : total times any node was added to the queue
      - enqueues_per_node : per-node breakdown of enqueue_count
      - total_relaxations : total successful dist[v] updates
      - early_stop        : False (queue exhaustion is normal termination)
      - elapsed_sec       : wall-clock time covering Steps 2 and 3 only
    """
    V = graph.V
    if not (0 <= source < V):
        raise ValueError(f"Source {source} is out of range [0, {V - 1}]")

    # Step 1 – initialise distances
    dist: list[float] = [math.inf] * V
    prev: list[int | None] = [None] * V
    dist[source] = 0.0

    # ── performance counters ─────────────────────────────────────────────────
    enqueue_count     = 0
    enqueues_per_node = [0] * V
    total_relaxations = 0

    # ── start timing (Steps 2 + 3 only — no I/O or graph construction) ───────
    t_start = time.perf_counter()

    # Step 2 – BFM queue-based relaxation
    # Only nodes whose distance improved are enqueued, so edges are only
    # processed from nodes that can propagate a useful update.
    in_queue: set[int] = {source}
    queue: deque[int]  = deque([source])
    enqueue_count += 1
    enqueues_per_node[source] += 1

    # Progress tracking — fires every 50K dequeues
    t_progress    = time.perf_counter()
    dequeue_count = 0
    INTERVAL      = 50_000

    print(f"  Starting BFM on {V:,} vertices ...")

    while queue:
        u = queue.popleft()
        in_queue.discard(u)
        dequeue_count += 1

        if dequeue_count % INTERVAL == 0:
            now     = time.perf_counter()
            elapsed = now - t_progress
            t_progress = now
            rate    = INTERVAL / elapsed if elapsed > 0 else 0
            print(f"  dequeued {dequeue_count:,} | queue: {len(queue):,} | "
                  f"relaxations: {total_relaxations:,} | "
                  f"rate: {rate:,.0f} nodes/sec")

        for v, w in graph.neighbors(u):
            new_dist = dist[u] + w
            if new_dist < dist[v]:
                dist[v] = new_dist
                prev[v] = u
                total_relaxations += 1
                if v not in in_queue:
                    queue.append(v)
                    in_queue.add(v)
                    enqueue_count += 1
                    enqueues_per_node[v] += 1

    print(f"  Queue drained after {dequeue_count:,} dequeues "
          f"(enqueue ratio: {enqueue_count / V:.2f}x)")

    # Step 3 – detect and propagate negative-weight cycles using one pass first
    cycle_found = False
    for u, v, w in graph.iter_edges():
        if dist[u] != math.inf and dist[u] + w < dist[v]:
            dist[v] = -math.inf
            prev[v] = u
            cycle_found = True

    # only propagate through all vertices if a cycle was actually detected
    if cycle_found:
        for _ in range(V - 1):
            for u, v, w in graph.iter_edges():
                if dist[u] == -math.inf or (dist[u] != math.inf and dist[u] + w < dist[v]):
                    dist[v] = -math.inf
                    prev[v] = u

    # ── stop timing ──────────────────────────────────────────────────────────
    elapsed_sec = time.perf_counter() - t_start

    import bellman_ford_moore_algorithm as _self
    _self.last_run["enqueue_count"]     = enqueue_count
    _self.last_run["enqueues_per_node"] = enqueues_per_node
    _self.last_run["total_relaxations"] = total_relaxations
    _self.last_run["early_stop"]        = False
    _self.last_run["elapsed_sec"]       = elapsed_sec

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