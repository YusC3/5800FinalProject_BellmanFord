"""
tests_runner.py
Runs BFM test cases defined in runner_config.json.
Data ingestion is handled separately via src/data_ingestion/.

Usage:
    python src/scripts/tests_runner.py -a        # run all tests
    python src/scripts/tests_runner.py -u        # run unit tests only
    python src/scripts/tests_runner.py -r        # run real-world tests only
    python src/scripts/tests_runner.py -u -s 2   # run unit test #2 only
    python src/scripts/tests_runner.py -r -s 1   # run real-world test #1 only
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

# ── Print helpers ─────────────────────────────────────────────────────────────

def header(text): print(f"\n{'═' * 60}\n  {text}\n{'═' * 60}")
def step(text):   print(f"  › {text}")
def ok(text):     print(f"  ✓ {text}")
def err(text):    print(f"  ✗ {text}", file=sys.stderr)

# ── Test runner ───────────────────────────────────────────────────────────────

def run_entries(entries):
    """Run a list of test entries. Returns (passed, failed)."""
    if not SINGLE_RUNNER.exists():
        err(f"run_single_test_case.py not found: {SINGLE_RUNNER}")
        sys.exit(1)

    passed, failed = 0, 0
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}

    for entry in entries:
        header(f"TEST [{entry['id']}]  {entry['label']}")
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

        result = subprocess.run(
            [sys.executable, str(SINGLE_RUNNER), str(input_path), str(output_path)],
            cwd=ROOT, env=env,
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
        description="Run BFM test cases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  tests_runner.py -a            run all tests
  tests_runner.py -u            run all unit tests
  tests_runner.py -r            run all real-world tests
  tests_runner.py -u -s 2      run unit test #2 only
  tests_runner.py -r -s 1      run real-world test #1 only
        """
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("-a", "--all",       action="store_true", help="Run all tests")
    mode.add_argument("-u", "--unit",      action="store_true", help="Run unit tests only")
    mode.add_argument("-r", "--real-world",action="store_true", help="Run real-world tests only")

    parser.add_argument("-s", "--single",  type=int, metavar="ID",
                        help="Run a single test by its ID within the selected category (-u or -r only)")
    args = parser.parse_args()

    # -s only valid with -u or -r
    if args.single and args.all:
        parser.error("-s/--single cannot be used with -a/--all")

    # Build the list of entries to run
    unit_entries       = CONFIG["unit_tests"]
    real_world_entries = CONFIG["real_world_tests"]

    if args.unit:
        pool = unit_entries
        category = "unit"
    elif args.real_world:
        pool = real_world_entries
        category = "real-world"
    else:
        pool = unit_entries + real_world_entries
        category = "all"

    if args.single:
        matches = [e for e in pool if e["id"] == args.single]
        if not matches:
            ids = [str(e["id"]) for e in pool]
            parser.error(f"No {category} test with id={args.single}. "
                         f"Available IDs: {', '.join(ids)}")
        entries = matches
    else:
        entries = pool

    # Run tests
    header("Running tests")
    passed, failed = run_entries(entries)

    # Summary
    header("SUMMARY")
    total = passed + failed
    if failed == 0:
        ok(f"All {total} test(s) ran without errors")
    else:
        err(f"{failed} / {total} test(s) failed")

    print()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()