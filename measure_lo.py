#!/usr/bin/env python3
"""
Memory benchmark for LibreOffice formula evaluation.
Measures total system memory including LibreOffice child process.
Uses psutil to track all processes in the process tree.
"""
import sys, subprocess, time, threading, json
import psutil
from pathlib import Path
import shutil

n = sys.argv[1] if len(sys.argv) > 1 else "10000"
input_path = Path(f"/tmp/benchmark/test_{n}.xlsx")

# Determine timeout based on input size (10 minutes for max/large tests)
timeout = 600 if n in ["max"] or "2sheet" in n else 120

# Extract row count for reporting
if n == "max":
    rows_report = 1048576
elif n.startswith("2sheet_"):
    rows_report = int(n.replace("2sheet_", ""))
else:
    rows_report = int(n)

input_dir = Path("/tmp/lo_mem_input")
output_dir = Path("/tmp/lo_mem_output")
input_dir.mkdir(exist_ok=True)
output_dir.mkdir(exist_ok=True)

def get_process_tree_rss(pid):
    """Get total RSS memory of process and all its children."""
    try:
        proc = psutil.Process(pid)
        total = proc.memory_info().rss
        for child in proc.children(recursive=True):
            try:
                total += child.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return total
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0

# ── Copy input file BEFORE monitoring (setup overhead) ──
tmp_in = input_dir / f"test_{n}.xlsx"
shutil.copy(input_path, tmp_in)

# ── Baseline memory before LibreOffice operation ──
self_pid = psutil.Process()
baseline_rss = get_process_tree_rss(self_pid.pid)

peak_rss = baseline_rss
peak_lock = threading.Lock()
stop_event = threading.Event()

def memory_monitor():
    """Poll memory every 50ms and track peak."""
    global peak_rss
    while not stop_event.is_set():
        current = get_process_tree_rss(self_pid.pid)
        with peak_lock:
            if current > peak_rss:
                peak_rss = current
        time.sleep(0.05)

monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
monitor_thread.start()

# ── LibreOffice evaluate ──
proc = subprocess.run([
    "libreoffice", "--headless", "--convert-to", "xlsx",
    "--outdir", str(output_dir), str(tmp_in)
], capture_output=True, timeout=timeout)

# ── Stop monitor ──
stop_event.set()
monitor_thread.join()

used_mb = (peak_rss - baseline_rss) / 1024 / 1024
peak_mb = peak_rss / 1024 / 1024

print(json.dumps({
    "rows": rows_report,
    "peakTotalMB": round(peak_mb, 1),
    "usedMB": round(used_mb, 1),  # net increase from baseline
    "baselineMB": round(baseline_rss / 1024 / 1024, 1),
}))
