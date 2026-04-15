# ──────────────────────────────────────────────
# Graph representations
# ──────────────────────────────────────────────

class AdjacencyListGraph:
    """
    Directed weighted graph stored as an adjacency list.

    edges[u] = list of (v, weight) tuples meaning u → v with given weight.
    """

    def __init__(self, num_vertices: int):
        self.V = num_vertices
        self.edges: list[list[tuple[int, float]]] = [[] for _ in range(num_vertices)]

    def add_edge(self, u: int, v: int, weight: float) -> None:
        """Add directed edge u → v with the given weight."""
        if not (0 <= u < self.V and 0 <= v < self.V):
            raise ValueError(f"Vertex indices must be in [0, {self.V - 1}]")
        self.edges[u].append((v, weight))

    def iter_edges(self):
        """Yield (u, v, weight) for every edge in the graph."""
        for u in range(self.V):
            for v, w in self.edges[u]:
                yield u, v, w

    def neighbors(self, u: int) -> list[tuple[int, float]]:
        """Return list of (v, weight) tuples for all edges out of u."""
        return self.edges[u]
    
    def __repr__(self) -> str:
        lines = [f"AdjacencyListGraph ({self.V} vertices)"]
        for u in range(self.V):
            for v, w in self.edges[u]:
                lines.append(f"  {u} → {v}  (weight {w})")
        return "\n".join(lines)


class AdjacencyMatrixGraph:
    """
    Directed weighted graph stored as an adjacency matrix.

    matrix[u][v] = weight of edge u → v, or None if no edge exists.
    """

    def __init__(self, num_vertices: int):
        self.V = num_vertices
        self.matrix: list[list[float | None]] = [
            [None] * num_vertices for _ in range(num_vertices)
        ]

    def add_edge(self, u: int, v: int, weight: float) -> None:
        """Add directed edge u → v with the given weight."""
        if not (0 <= u < self.V and 0 <= v < self.V):
            raise ValueError(f"Vertex indices must be in [0, {self.V - 1}]")
        self.matrix[u][v] = weight

    def iter_edges(self):
        """Yield (u, v, weight) for every edge in the graph."""
        for u in range(self.V):
            for v in range(self.V):
                w = self.matrix[u][v]
                if w is not None:
                    yield u, v, w

    def neighbors(self, u: int) -> list[tuple[int, float]]:
        """Return list of (v, weight) tuples for all edges out of u."""
        return [(v, w) for v, w in enumerate(self.matrix[u]) if w is not None]

    def __repr__(self) -> str:
        lines = [f"AdjacencyMatrixGraph ({self.V} vertices)"]
        for u in range(self.V):
            for v in range(self.V):
                w = self.matrix[u][v]
                if w is not None:
                    lines.append(f"  {u} → {v}  (weight {w})")
        return "\n".join(lines)