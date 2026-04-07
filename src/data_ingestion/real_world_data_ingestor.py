"""
real_world_data_ingestor.py
Downloads, decompresses, and converts real-world datasets into the
batch_runner input format, using settings from src/config.json.

Usage:
    python src/scripts/real_world_data_ingestor.py                  # download + convert all
    python src/scripts/real_world_data_ingestor.py --skip-download  # convert existing raw files only
"""

import argparse
import gzip
import json
import random
import shutil
import sys
import urllib.request
from pathlib import Path

# ── Load config ───────────────────────────────────────────────────────────────

ROOT        = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = Path(__file__).resolve().parent / "ingestion_config.json"

if not CONFIG_PATH.exists():
    print(f"Error: ingestion_config.json not found at {CONFIG_PATH}", file=sys.stderr)
    sys.exit(1)

with CONFIG_PATH.open(encoding="utf-8") as f:
    CONFIG = json.load(f)

RAW_DIR      = ROOT / CONFIG["paths"]["raw_input"]
REAL_OUT_DIR = ROOT / CONFIG["paths"]["converted_output"]

# ── Print helpers ─────────────────────────────────────────────────────────────

def header(text): print(f"\n{'═' * 60}\n  {text}\n{'═' * 60}")
def step(text):   print(f"  › {text}")
def ok(text):     print(f"  ✓ {text}")
def err(text):    print(f"  ✗ {text}", file=sys.stderr)

def progress_bar(downloaded, total, width=36):
    if total <= 0:
        print(f"\r    {downloaded // 1024} KB downloaded...", end="", flush=True)
        return
    pct  = downloaded / total
    done = int(width * pct)
    bar  = "█" * done + "░" * (width - done)
    print(f"\r    [{bar}] {pct*100:5.1f}%  {downloaded//1024} / {total//1024} KB",
          end="", flush=True)

# ── Download & decompress ─────────────────────────────────────────────────────

def download(url, dest):
    step(f"Downloading {dest.name}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            total, downloaded = int(resp.headers.get("Content-Length", 0)), 0
            with open(dest, "wb") as f:
                while buf := resp.read(8192):
                    f.write(buf)
                    downloaded += len(buf)
                    progress_bar(downloaded, total)
        print()
        return True
    except Exception as e:
        print(); err(f"Download failed: {e}"); return False

def decompress(gz_path, out_path):
    step(f"Decompressing {gz_path.name}")
    try:
        with gzip.open(gz_path, "rb") as f_in, open(out_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        return True
    except Exception as e:
        err(f"Decompression failed: {e}"); return False

# ── Converters ────────────────────────────────────────────────────────────────

def convert_dimacs(input_path, output_path, source):
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
        err(f"Conversion failed: {e}"); return False

def convert_snap(input_path, output_path, source_orig, seed, min_w, max_w):
    step(f"Converting {input_path.name} → {output_path.name}")
    raw, nodes = [], set()
    try:
        with open(input_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
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
        ok(f"{len(nodes):,} vertices, {len(edges):,} edges "
           f"(weights [{min_w},{max_w}], seed={seed})")
        return True
    except Exception as e:
        err(f"Conversion failed: {e}"); return False

# ── Pipeline ──────────────────────────────────────────────────────────────────

def run(skip_download=False):
    """
    Download, decompress, and convert all datasets defined in config.json.
    Returns a list of dataset names that failed.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REAL_OUT_DIR.mkdir(parents=True, exist_ok=True)
    failed = []

    for d in CONFIG["datasets"]["dimacs"]:
        header(f"DIMACS  {d['name']}  —  {d['desc']}")
        out = REAL_OUT_DIR / f"{d['name']}.txt"
        if out.exists():
            ok(f"Already converted: {out.name}  (delete to re-run)"); continue

        gz = RAW_DIR / d["gz_file"]
        gr = RAW_DIR / d["gr_file"]

        if not skip_download and not gz.exists():
            if not download(d["url"], gz):
                failed.append(d["name"]); continue
        if not gr.exists():
            if not decompress(gz, gr):
                failed.append(d["name"]); continue
        if not convert_dimacs(gr, out, d["source"]):
            failed.append(d["name"])

    for d in CONFIG["datasets"]["snap"]:
        header(f"SNAP  {d['name']}  —  {d['desc']}")
        out = REAL_OUT_DIR / f"{d['name']}.txt"
        if out.exists():
            ok(f"Already converted: {out.name}  (delete to re-run)"); continue

        gz  = RAW_DIR / d["gz_file"]
        txt = RAW_DIR / d["txt_file"]

        if not skip_download and not gz.exists():
            if not download(d["url"], gz):
                failed.append(d["name"]); continue
        if not txt.exists():
            if not decompress(gz, txt):
                failed.append(d["name"]); continue
        if not convert_snap(txt, out, d["source"],
                            d["seed"], d["min_weight"], d["max_weight"]):
            failed.append(d["name"])

    return failed

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download and convert real-world datasets for BFM testing."
    )
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip downloading; convert already-present raw files only")
    args = parser.parse_args()

    failed = run(skip_download=args.skip_download)

    header("SUMMARY")
    if failed:
        err(f"Datasets that failed: {', '.join(failed)}")
        sys.exit(1)
    else:
        ok("All datasets prepared successfully")
        sys.exit(0)