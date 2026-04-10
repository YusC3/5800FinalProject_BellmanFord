# Bellman-Ford-Moore — Log File Guide

Each `.log` file corresponds to one input test case file and contains results
for all test cases found within it.

---

## File Header

Appears once at the top of every log file.

```
Bellman-Ford-Moore — Batch Results
Generated   : 2026-04-10 14:18:26   ← timestamp of the run
Input file  : .../test_cases.txt    ← source input file
Test cases  : 5                     ← total number of test cases in the file

  I/O Overhead (shared across all test cases)
  io_read_sec : 0.000012 s          ← time to read the entire input file from disk
```

`io_read_sec` is shared because the input file is read once upfront for all test cases.

---

## Per Test Case Block

Each test case is separated by a `====` divider and contains three sections.

### 1. Graph Details
Describes the input graph for this test case.

| Field          | Description                                      |
|----------------|--------------------------------------------------|
| Representation | `LIST` (adjacency list) or `MATRIX` (adjacency matrix) |
| Vertices       | Number of vertices \|V\|                         |
| Edges          | Number of edges \|E\|                            |
| Source         | Source vertex the algorithm starts from          |

### 2. Performance
Metrics collected from inside the BFM algorithm itself.

| Field        | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| rounds       | Number of outer loop iterations completed (max possible: \|V\| - 1)        |
| relaxations  | Total number of times a vertex distance was successfully updated            |
| early_stop   | `True` if Moore's optimisation triggered — no updates occurred in a round, so the algorithm exited before reaching \|V\| - 1 rounds |
| elapsed_sec  | Wall-clock time of the core algorithm only (Steps 2 and 3), excludes I/O and graph construction |

### 3. Performance Overhead
Time spent on setup work outside the algorithm itself.

| Field           | Description                                              |
|-----------------|----------------------------------------------------------|
| graph_build_sec | Time to construct the graph object and add all edges     |

### 4. Correctness Results
A table of shortest-path results from the source vertex.

| Column          | Description                                                      |
|-----------------|------------------------------------------------------------------|
| Vertex          | Target vertex index                                              |
| Distance        | Shortest distance from source (`inf` = unreachable)             |
| Path from source| Sequence of vertices on the shortest path (`<unreachable>` if no path exists, `<cycle detected>` if a negative-weight cycle affects this vertex) |

If a negative-weight cycle is detected, the correctness table is replaced with:
```
*** Negative-weight cycle detected — no solution. ***
```

---

## Example Block

```
============================================================
TEST CASE #1
============================================================

  Graph Details
  Representation     : LIST
  Vertices           : 6
  Edges              : 9
  Source             : 0

  Performance
  rounds             : 3
  relaxations        : 7
  early_stop         : True
  elapsed_sec        : 0.000021 s

  Performance Overhead
  graph_build_sec    : 0.000008 s

  Vertex     Distance        Path from source
  --------------------------------------------------
  0          0.0             0
  1          -1.0            0 → 1
  2          3.0             0 → 1 → 2
  3          1.0             0 → 1 → 3
  4          1.0             0 → 1 → 4
  5          3.0             0 → 1 → 3 → 5
```
