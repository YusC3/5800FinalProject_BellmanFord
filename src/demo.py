# ──────────────────────────────────────────────
# Demo / interactive driver
# ──────────────────────────────────────────────

from bellman_ford_moore_algorithm import bellman_ford_moore, print_results
from graph import AdjacencyListGraph, AdjacencyMatrixGraph


def _build_example(GraphClass):
    """
    Example graph (6 vertices):

        0 --(-1)--> 1 --(4)--> 2
        |                      ^
       (4)                    (5)
        |                      |
        v                      |
        3 --(3)----------> 4 --(2)--> 5
        |                             ^
        +-----------(2)---------------+
    """
    g = GraphClass(6)
    g.add_edge(0, 1, -1)
    g.add_edge(0, 3,  4)
    g.add_edge(1, 2,  4)
    g.add_edge(1, 3,  2)
    g.add_edge(1, 4,  2)
    g.add_edge(3, 4,  3)
    g.add_edge(4, 2,  5)
    g.add_edge(4, 5,  2)
    g.add_edge(3, 5,  2)   # direct shortcut
    return g


def main():
    print("=" * 60)
    print("  Bellman-Ford-Moore Shortest Path Algorithm")
    print("=" * 60)

    # ── Choose representation ──
    print("\nChoose graph representation:")
    print("  1) Adjacency List")
    print("  2) Adjacency Matrix")
    choice = input("Enter 1 or 2 [default: 1]: ").strip() or "1"

    GraphClass = AdjacencyListGraph if choice == "1" else AdjacencyMatrixGraph
    rep_name = "Adjacency List" if choice == "1" else "Adjacency Matrix"
    print(f"\nUsing: {rep_name}")

    # ── Choose input method ──
    print("\nInput method:")
    print("  1) Use built-in example graph  (6 vertices)")
    print("  2) Enter your own graph")
    inp = input("Enter 1 or 2 [default: 1]: ").strip() or "1"

    if inp == "1":
        graph = _build_example(GraphClass)
        source = 0
        print(f"\n{graph}")
        print(f"\nSource vertex: {source}")
    else:
        V = int(input("\nNumber of vertices: ").strip())
        E = int(input("Number of edges: ").strip())
        graph = GraphClass(V)
        print("Enter each edge as:  u  v  weight")
        for _ in range(E):
            parts = input("  > ").strip().split()
            u, v, w = int(parts[0]), int(parts[1]), float(parts[2])
            graph.add_edge(u, v, w)
        source = int(input(f"Source vertex [0-{V-1}]: ").strip())

    # ── Run algorithm ──
    dist, prev = bellman_ford_moore(graph, source)

    # ── Display results ──
    print_results(dist, prev, source)
    print()


if __name__ == "__main__":
    main()