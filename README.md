# Memory Benchmark: LibreOffice vs JS xlsx-calc

A fair comparison of peak memory usage between LibreOffice and JavaScript (SheetJS + xlsx-calc) for Excel formula evaluation.

## Key Finding

LibreOffice uses approximately **2x more peak memory** than JavaScript across all data scales.

```
Peak Memory Comparison

Rows     JS Peak (MB)    LibreOffice Peak (MB)    Ratio (LO/JS)
────────────────────────────────────────────────────────────────
 10K        104.9              234.3              2.2x
 50K        164.4              304.2              1.9x
100K        218.0              427.1              2.0x
200K        344.3              720.4              2.1x
```

## Methodology

This benchmark uses a **fair measurement approach** that addresses common pitfalls in memory comparisons:

### Fair Measurement Principles

1. **Peak Memory Tracking**: Both LibreOffice and JS continuously track peak RSS during operations, not just a final snapshot
2. **Baseline Subtraction**: Runtime overhead (Python interpreter, V8 engine) is subtracted to show net memory used for the actual work
3. **Process Tree Measurement**: LibreOffice measures the entire process tree (Python + soffice child process)

### What's Being Measured

| Metric | Description |
|--------|-------------|
| `peakTotalMB` | Peak RSS memory during the entire operation |
| `usedMB` | Net memory increase from baseline (actual work) |
| `baselineMB` | Memory before any operations (runtime overhead) |

### Net Memory Comparison (usedMB)

When comparing only the memory used for actual Excel processing:

| Rows | JS Used (MB) | LibreOffice Used (MB) | Ratio |
|------|--------------|----------------------|-------|
| 10K  | 36.7         | 210.9                | 5.7x  |
| 50K  | 92.8         | 280.8                | 3.0x  |
| 100K | 149.5        | 403.7                | 2.7x  |
| 200K | 272.7        | 697.0                | 2.6x  |

## Quick Start (Docker/Podman)

The easiest way to run the benchmark is with Docker or Podman:

```bash
# Build the image
podman build -t lo-vs-xlsx-benchmark .

# Run the full benchmark
podman run --rm lo-vs-xlsx-benchmark

# Run individual tests
podman run --rm lo-vs-xlsx-benchmark python3 measure_lo.py 10000
podman run --rm lo-vs-xlsx-benchmark node measure_js.mjs 10000
```

## Manual Setup

### Prerequisites

```bash
# Python
pip install openpyxl psutil

# Node.js
npm install xlsx xlsx-calc

# LibreOffice
sudo apt install libreoffice  # Ubuntu/Debian
brew install libreoffice      # macOS
```

### Running the Benchmark

```bash
# LibreOffice memory (process tree)
for n in 10000 50000 100000 200000; do
    python3 measure_lo.py $n
done

# JS memory
for n in 10000 50000 100000 200000; do
    node measure_js.mjs $n
done
```

## Output Format

Both measurement scripts output JSON with consistent format:

```json
{
  "rows": 10000,
  "peakTotalMB": 234.3,
  "usedMB": 210.9,
  "baselineMB": 23.4
}
```

- `peakTotalMB` — Peak RSS memory during entire operation
- `usedMB` — Net memory increase from baseline (actual Excel work)
- `baselineMB` — Memory before any operations (runtime overhead)

## Files

| File | Description |
|------|-------------|
| `measure_lo.py` | Measure LibreOffice memory including child processes |
| `measure_js.mjs` | Measure JS memory with peak tracking |
| `Dockerfile` | Container image for reproducible benchmarks |
| `docker-entrypoint.sh` | Automated benchmark script |

## Why Previous Measurements Were Wrong

Many benchmarks incorrectly measure LibreOffice memory using `tracemalloc` or Python heap profilers, which only see the Python process:

```python
# ❌ Wrong — doesn't include LibreOffice child process
tracemalloc.start()
subprocess.run(["libreoffice", "--headless", ...])
current, peak = tracemalloc.get_traced_memory()  # Only sees Python heap
```

This results in unrealistically low values (1.5-15.5 MB) because the LibreOffice process with ~300-400 MB overhead isn't counted.

The correct approach uses `psutil` to measure the entire process tree:

```python
# ✅ Correct — measures all processes
def get_process_tree_rss(pid):
    proc = psutil.Process(pid)
    total = proc.memory_info().rss
    for child in proc.children(recursive=True):
        total += child.memory_info().rss
    return total
```
