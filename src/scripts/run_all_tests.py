"""
run_all_tests.py
Downloads, converts, and runs all test cases for the BFM project.
Works on macOS, Linux, and Windows (Python 3.6+, no external dependencies).

Usage:
    python scripts/run_all_tests.py                  # full pipeline
    python scripts/run_all_tests.py --skip-download  # skip download, use existing raw files
    python scripts/run_all_tests.py --skip-data      # skip all data setup, only run tests
    python scripts/run_all_tests.py --tests-only     # alias for --skip-data
"""

import argparse
import gzip
import os
import random
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

ROOT        = Path(__file__).parent.parent
BATCH_RUNNER = ROOT / "src" / "batch_runner.py"
RAW_DIR     = ROOT / "test" / "real_world" / "raw"
OUT_DIR     = ROOT / "test" / "real_world"
RESULTS_DIR = ROOT / "results"

DIMACS_DATASETS = [
    {
        "name":    "road-NY",
        "url":     "http://www.diag.uniroma1.it/challenge9/data/USA-road-t/USA-road-t.NY.gr.gz",
        "gz_file": "USA-road-t.NY.gr.gz",
        "gr_file": "USA-road-t.NY.gr",
        "source":  0,
        "desc":    "New York road network (264K nodes, 733K edges)",
    },
    {
        "name":    "road-BAY",
        "url":     "http://www.diag.uniroma1.it/challenge9/data/USA-road-t/USA-road-t.BAY.gr.gz",
        "gz_file": "USA-road-t.BAY.gr.gz",
        "gr_file": "USA-road-t.BAY.gr",
        "source":  0,
        "desc":    "San Francisco Bay road network (321K nodes, 800K edges)",
    },
]

SNAP_DATASETS = [
    {
        "name":     "p2p-gnutella",
        "url":      "https://snap.stanford.edu/data/p2p-Gnutella04.txt.gz",
        "gz_file":  "p2p-Gnutella04.txt.gz",
        "txt_file": "p2p-Gnutella04.txt",
        "source":   None,
        "seed":     42,
        "min_w":    1,
        "max_w":    100,
        "desc":     "Gnutella P2P network (10K nodes, 40K edges)",
    },
]

# Test files to run, in order. Each entry is (label, input_path).
TEST_FILES = [
    ("Unit — constructed test cases",   ROOT / "test" / "unit" / "test_cases.txt"),
    ("Unit — easy instances", ROOT / "test" / "unit" / "easy_instances.txt"),
    ("Real — SNAP - P2P Gnutella",   OUT_DIR / "p2p-gnutella.txt"),
    ("Real — DIMACS - Road NY",        OUT_DIR / "road-NY.txt"),
    ("Real — DIMACS - Road BAY",       OUT_DIR / "road-BAY.txt"),
]

# ── Printing helpers ───────────────────────────────────────────────────────────

def header(text):
    print(f"\n{'═' * 60}")
    print(f"  {text}")
    print(f"{'═' * 60}")

def step(text):
    print(f"  › {text}")

def ok(text):
    print(f"  ✓ {text}")

def err(text):
    print(f"  ✗ {text}", file=sys.stderr)

def progress_bar(downloaded, total, width=36):
    if total <= 0:
        print(f"\r    {downloaded // 1024} KB downloaded...", end="", flush=True)
        return
    pct  = downloaded / total
    done = int(width * pct)
    bar  = "█" * done + "░" * (width - done)
    print(f"\r    [{bar}] {pct*100:5.1f}%  "
          f"{downloaded//1024} / {total//1024} KB", end="", flush=True)

# ── Download & decompress ─────────────────────────────────────────────────────

def download(url: str, dest: Path) -> bool:
    step(f"Downloading {dest.name}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            chunk, downloaded = 8192, 0
            with open(dest, "wb") as f:
                while True:
                    buf = resp.read(chunk)
                    if not buf:
                        break
                    f.write(buf)
                    downloaded += len(buf)
                    progress_bar(downloaded, total)
        print()
        return True
    except Exception as e:
        print()
        err(f"Download failed: {e}")
        return False

def decompress(gz_path: Path, out_path: Path) -> bool:
    step(f"Decompressing {gz_path.name}")
    try:
        with gzip.open(gz_path, "rb") as f_in, open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return True
    except Exception as e:
        err(f"Decompression failed: {e}")
        return False

# ── Converters ────────────────────────────────────────────────────────────────

def convert_dimacs(input_path: Path, output_path: Path, source: int) -> bool:
    step(f"Converting {input_path.name} → {output_path.name}")
    edges, n_v = [], 0
    try:
        with open(input_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("c"):
                    continue
                if line.startswith("p"):
                    n_v = int(line.split()[2])
                elif line.startswith("a"):
                    p = line.split()
                    edges.append((int(p[1]) - 1, int(p[2]) - 1, int(p[3])))
        with open(output_path, "w") as f:
            f.write(f"LIST\n{n_v}\n{len(edges)}\n")
            for u, v, w in edges:
                f.write(f"{u} {v} {w}\n")
            f.write(f"{source}\n")
        ok(f"{n_v:,} vertices, {len(edges):,} edges")
        return True
    except Exception as e:
        err(f"Conversion failed: {e}")
        return False

def convert_snap(input_path: Path, output_path: Path,
                 source_orig, seed, min_w, max_w) -> bool:
    step(f"Converting {input_path.name} → {output_path.name}")
    raw, nodes = [], set()
    try:
        with open(input_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                u, v = int(parts[0]), int(parts[1])
                if u != v:
                    raw.append((u, v))
                    nodes.update([u, v])
        id_map = {n: i for i, n in enumerate(sorted(nodes))}
        rng    = random.Random(seed)
        edges  = [(id_map[u], id_map[v], rng.randint(min_w, max_w)) for u, v in raw]
        source = id_map[source_orig] if source_orig is not None else 0
        with open(output_path, "w") as f:
            f.write(f"LIST\n{len(nodes)}\n{len(edges)}\n")
            for u, v, w in edges:
                f.write(f"{u} {v} {w}\n")
            f.write(f"{source}\n")
        ok(f"{len(nodes):,} vertices, {len(edges):,} edges  "
           f"(weights [{min_w},{max_w}], seed={seed})")
        return True
    except Exception as e:
        err(f"Conversion failed: {e}")
        return False

# ── Data pipeline ─────────────────────────────────────────────────────────────

def run_data_pipeline(skip_download: bool) -> list[str]:
    """Returns list of dataset names that failed."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failed = []

    for d in DIMACS_DATASETS:
        header(f"DIMACS  {d['name']}  —  {d['desc']}")
        out = OUT_DIR / f"{d['name']}.txt"
        if out.exists():
            ok(f"Already converted: {out.name}  (delete to re-run)")
            continue

        gz  = RAW_DIR / d["gz_file"]
        gr  = RAW_DIR / d["gr_file"]

        if not skip_download and not gz.exists():
            if not download(d["url"], gz):
                failed.append(d["name"]); continue

        if not gr.exists():
            if not decompress(gz, gr):
                failed.append(d["name"]); continue

        if not convert_dimacs(gr, out, d["source"]):
            failed.append(d["name"])

    for d in SNAP_DATASETS:
        header(f"SNAP  {d['name']}  —  {d['desc']}")
        out = OUT_DIR / f"{d['name']}.txt"
        if out.exists():
            ok(f"Already converted: {out.name}  (delete to re-run)")
            continue

        gz  = RAW_DIR / d["gz_file"]
        txt = RAW_DIR / d["txt_file"]

        if not skip_download and not gz.exists():
            if not download(d["url"], gz):
                failed.append(d["name"]); continue

        if not txt.exists():
            if not decompress(gz, txt):
                failed.append(d["name"]); continue

        if not convert_snap(txt, out, d["source"],
                            d["seed"], d["min_w"], d["max_w"]):
            failed.append(d["name"])

    return failed

# ── Test runner ───────────────────────────────────────────────────────────────

def run_tests() -> tuple[int, int]:
    """Returns (passed, failed) counts."""
    if not BATCH_RUNNER.exists():
        err(f"batch_runner.py not found: {BATCH_RUNNER}")
        sys.exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    passed, failed = 0, 0

    for label, input_path in TEST_FILES:
        header(f"TEST  {label}")
        if not input_path.exists():
            err(f"Input file not found, skipping: {input_path}")
            failed += 1
            continue

        output_path = RESULTS_DIR / f"{input_path.stem}_results.txt"
        step(f"Input  : {input_path.relative_to(ROOT)}")
        step(f"Output : {output_path.relative_to(ROOT)}")
        print()

        result = subprocess.run(
            [sys.executable, str(BATCH_RUNNER), str(input_path), str(output_path)],
            cwd=ROOT,
        )
        print()
        if result.returncode == 0:
            ok(f"Results written to {output_path.name}")
            passed += 1
        else:
            err(f"batch_runner.py exited with code {result.returncode}")
            failed += 1

    return passed, failed

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Download, convert, and run all BFM test cases."
    )
    parser.add_argument("--skip-download", action="store_true",
                        help="Convert already-present raw files; do not fetch from network")
    parser.add_argument("--skip-data", "--tests-only", action="store_true",
                        help="Skip all data setup and go straight to running tests")
    args = parser.parse_args()

    data_errors = []
    if not args.skip_data:
        header("STEP 1 / 2  —  Data setup")
        data_errors = run_data_pipeline(skip_download=args.skip_download)

    header("STEP 2 / 2  —  Running tests")
    passed, failed = run_tests()

    # ── Summary ──────────────────────────────────────────────────────────────
    header("SUMMARY")
    if data_errors:
        err(f"Datasets that failed to prepare: {', '.join(data_errors)}")
    else:
        ok("All datasets prepared successfully")

    total = passed + failed
    if failed == 0:
        ok(f"All {total} test files ran without errors")
    else:
        err(f"{failed} / {total} test files failed")

    print()
    sys.exit(1 if (data_errors or failed) else 0)


if __name__ == "__main__":
    main()
