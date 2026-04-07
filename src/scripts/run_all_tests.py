"""
run_all_tests.py
Runs all BFM test cases defined in config.json, optionally triggering
real-world data ingestion first via real_world_data_ingestion.py.

Usage:
    python src/scripts/run_all_tests.py                  # full pipeline
    python src/scripts/run_all_tests.py --skip-download  # skip download, use existing raw files
    python src/scripts/run_all_tests.py --skip-data      # skip data setup, run tests only
    python src/scripts/run_all_tests.py --tests-only     # alias for --skip-data
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ── Load config ───────────────────────────────────────────────────────────────

ROOT        = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "runner_config.json"

if not CONFIG_PATH.exists():
    print(f"Error: runner_config.json not found at {CONFIG_PATH}", file=sys.stderr)
    sys.exit(1)

with CONFIG_PATH.open(encoding="utf-8") as f:
    CONFIG = json.load(f)

SINGLE_RUNNER = ROOT / CONFIG["paths"]["single_runner"]
INGESTOR      = ROOT / CONFIG["paths"]["ingestor"]


# ── Print helpers ─────────────────────────────────────────────────────────────

def header(text): print(f"\n{'═' * 60}\n  {text}\n{'═' * 60}")
def step(text):   print(f"  › {text}")
def ok(text):     print(f"  ✓ {text}")
def err(text):    print(f"  ✗ {text}", file=sys.stderr)

# ── Data pipeline ─────────────────────────────────────────────────────────────

def run_data_pipeline(skip_download):
    if not INGESTOR.exists():
        err(f"real_world_data_ingestion.py not found: {INGESTOR}")
        return False

    cmd = [sys.executable, str(INGESTOR)]
    if skip_download:
        cmd.append("--skip-download")

    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode == 0

# ── Test runner ───────────────────────────────────────────────────────────────

def run_tests():
    if not SINGLE_RUNNER.exists():
        err(f"run_single_test_case.py not found: {SINGLE_RUNNER}")
        sys.exit(1)

    passed, failed = 0, 0

    for entry in CONFIG["test_files"]:
        header(f"TEST  {entry['label']}")
        input_path  = ROOT / entry["input"]
        output_path = ROOT / entry["output"]

        if not input_path.exists():
            err(f"Input file not found, skipping: {input_path}")
            failed += 1
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)
        step(f"Input  : {entry['input']}")
        step(f"Output : {entry['output']}")
        print()

        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        result = subprocess.run(
            [sys.executable, str(SINGLE_RUNNER),
             str(input_path), str(output_path)],
            cwd=ROOT,
            env=env,
        )
        print()
        if result.returncode == 0:
            ok(f"Results written to {output_path.name}")
            passed += 1
        else:
            err(f"run_single_test_case.py exited with code {result.returncode}")
            failed += 1

    return passed, failed

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Download, convert, and run all BFM test cases."
    )
    parser.add_argument("--skip-download", action="store_true",
                        help="Pass --skip-download through to the ingestor")
    parser.add_argument("--skip-data", "--tests-only", action="store_true",
                        help="Skip data ingestion and go straight to running tests")
    args = parser.parse_args()

    data_ok = True
    if not args.skip_data:
        header("STEP 1 / 2  —  Data ingestion")
        data_ok = run_data_pipeline(skip_download=args.skip_download)

    header("STEP 2 / 2  —  Running tests")
    passed, failed = run_tests()

    header("SUMMARY")
    if not data_ok:
        err("One or more datasets failed to prepare — see above for details")
    else:
        ok("All datasets prepared successfully")

    total = passed + failed
    if failed == 0:
        ok(f"All {total} test files ran without errors")
    else:
        err(f"{failed} / {total} test files failed")

    print()
    sys.exit(1 if (not data_ok or failed) else 0)


if __name__ == "__main__":
    main()