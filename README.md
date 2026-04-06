# Bellman-Ford-Moore — Empirical Analysis
CS 5800 Algorithms · Northeastern University

Empirical analysis of the Bellman-Ford-Moore (BFM) shortest-path algorithm across
constructed easy/hard instances, random graphs, and real-world datasets. Measures
enqueue count, queue passes, and wall-clock time to evaluate practical performance
against theoretical O(VE) worst-case bounds.

---

## Quick Start

```bash
# 1. Download and convert all datasets, then run all test cases
python scripts/run_all.py

# 2. Or run a single input/output pair manually
python src/batch_runner.py <input_file> <output_file>
```

Results are written to `results/`.

---

## Project Structure

```
project/
├── src/
│   ├── batch_runner.py           # Entry point — reads test file, writes results
│   ├── bellman_ford_algorithm.py # BFM implementation with performance counters
│   ├── graph.py                  # AdjacencyListGraph and AdjacencyMatrixGraph
│   └── main.py
├── test/
│   ├── unit/
│   │   ├── test_cases.txt        # Correctness tests (negative edges, cycles, disconnected)
│   │   ├── easy_instances.txt    # Constructed best-case inputs (chains, DAGs, trees)
│   │   └── hard_instances.txt    # Constructed worst-case inputs (backward negative edges)
│   └── real_world/               # Large external datasets — see setup below
│       ├── road-NY.txt
│       ├── road-BAY.txt
│       └── p2p-gnutella.txt
├── scripts/
│   ├── run_all.py                # Downloads, converts, and runs all test cases
│   ├── convert_dimacs.py         # Converts DIMACS .gr files to project format
│   └── convert_snap.py           # Converts SNAP edge lists to project format
└── results/                      # Output files written here (git-ignored)
```

---

## Test Input Format

All test files use a shared plaintext format. Multiple test cases can be placed
in a single file, separated by blank lines. Lines beginning with `#` are ignored.

```
LIST|MATRIX
<num_vertices>
<num_edges>
<src> <dst> <weight>
...
<source_vertex>
```

**Example — single test case:**
```
# Simple triangle
LIST
3
3
0 1 5
1 2 3
0 2 10
0
```

---

## Test Cases

### Unit Tests (`test/unit/`)

`test_cases.txt` — 5 hand-crafted correctness tests covering:
- Negative edge weights
- Negative-weight cycle detection
- Non-zero source vertex
- Disconnected graph (unreachable vertices)
- Both LIST and MATRIX representations

`easy_instances.txt` — 6 constructed best-case instances where every vertex is
enqueued exactly once. Establishes the O(V) empirical lower bound. Includes
linear chains, star graphs, binary trees, and forward DAGs.

`hard_instances.txt` — Constructed worst-case instances using backward negative
edges that force repeated re-enqueuing. Designed to approach the O(V²) upper
bound on enqueue count.

### Real-World Datasets (`test/real_world/`)

Large datasets are not included in this repository. Run the setup script to
download and convert them automatically:

```bash
python scripts/run_all.py
```

Or to convert already-downloaded raw files without re-fetching:

```bash
python scripts/run_all.py --skip-download
```

| Dataset | Source | Vertices | Edges | Notes |
|---|---|---|---|---|
| `road-NY.txt` | DIMACS 9th Challenge | 264,346 | 733,846 | NYC road network, travel-time weights |
| `road-BAY.txt` | DIMACS 9th Challenge | 321,270 | 800,172 | SF Bay road network, travel-time weights |
| `p2p-gnutella.txt` | SNAP | 10,876 | 39,994 | P2P network, synthetic weights (seed=42, range [1,100]) |

Raw archives are saved to `test/real_world/raw/` and can be deleted after
conversion with no effect on the test files.


#### About the datasets

**DIMACS 9th Implementation Challenge — Shortest Paths**
The DIMACS (Center for Discrete Mathematics and Theoretical Computer Science)
9th Implementation Challenge was a benchmark competition focused specifically on
shortest-path algorithms. In its datasets, nodes represent road intersections and edges represent
road segments, with integer weights corresponding to travel times. These graphs are
sparse (average degree ~2.8), nearly planar, and have a structure that tends to
be favorable for BFM since updates flow mostly forward and nodes are rarely re-enqueued.
Data and documentation are available at:
http://www.diag.uniroma1.it/challenge9/download.shtml

**SNAP — Stanford Large Network Dataset Collection**
SNAP (Stanford Network Analysis Platform) is a general-purpose graph analysis
library and accompanying public dataset collection maintained by Jure Leskovec
at Stanford. It covers a wide range of real-world network types including social,
communication, citation, web, and peer-to-peer networks. The Gnutella dataset
used here is a snapshot of the Gnutella peer-to-peer file-sharing network, where
nodes are hosts and directed edges represent connections between them. Unlike road
networks, P2P networks have small-world properties such as short diameter and hub nodes
with high degree, making them more challenging for BFM. Because
SNAP graphs are natively unweighted, integer weights were assigned uniformly at
random (seed=42, range [1, 100]) for use in this project.
Data and documentation are available at:
https://snap.stanford.edu/data/

---

## Performance Counters

The BFM implementation records the following metrics on every run:

| Metric | Description | Theoretical range |
|---|---|---|
| Enqueue count | Total times any node was added to the queue | V (best) → V² (worst) |
| Enqueues per node | Per-node breakdown of the above | 1 (best) → V (worst) |
| Queue passes | Number of full sweeps through the queue | 1 (best) → V−1 (worst) |
| Wall-clock time | Measured with `time.perf_counter_ns()`, I/O excluded | — |

To evaluate scaling behavior, compute the **enqueue ratio**:

```
ratio = enqueue_count / V
```

A ratio near 1 indicates best-case behavior. A ratio growing proportionally
with V indicates worst-case O(V²) behavior.

---

## Replicating Results

All enqueue counts and pass counts are deterministic and will match exactly
across environments. Wall-clock times will vary by machine.

```bash
# Full pipeline (download + convert + run)
python scripts/run_all.py

# Skip data setup if datasets are already prepared
python scripts/run_all.py --tests-only
```

Each test file produces a corresponding results file in `results/`:

```
results/
├── test_cases_results.txt
├── easy_instances_results.txt
├── hard_instances_results.txt
├── road-NY_results.txt
├── road-BAY_results.txt
└── p2p-gnutella_results.txt
```