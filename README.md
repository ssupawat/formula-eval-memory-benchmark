# Memory Benchmark: LibreOffice vs JS xlsx-calc vs DuckDB

A comparison of peak memory usage and evaluation time between LibreOffice, JavaScript (SheetJS + xlsx-calc), and DuckDB for Excel formula evaluation.

## Key Findings

**Memory:** DuckDB uses **5-15x less memory** than JS and **10-20x less** than LibreOffice at scale.

**Time:** JS is fastest for small datasets (<100K rows). DuckDB is competitive at larger scales. Formula evaluation itself is extremely fast (<0.02s even for 1M rows).

**I/O dominates:** Streaming XLSX conversion (xlsx2csv + xlsxwriter) accounts for ~99% of DuckDB's runtime.

```
Standard Tests (1 Sheet)

Rows     DuckDB Time (s)    JS Time (s)    LO Time (s)    DuckDB Peak (MB)    JS Peak (MB)    LO Peak (MB)
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 10K        0.23               0.12            2.24             69                 103               197
 50K        0.80               0.53            1.96             76                 161               242
100K        1.56               0.91            1.64             78                 216               283
200K        3.01               1.94            2.37             86                 407               406
```

```
Max Rows (1 Sheet)

Rows         DuckDB Time (s)    JS Time (s)    LO Time (s)    DuckDB Peak (MB)    JS Peak (MB)    LO Peak (MB)
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
1,048,576       15.93             13.48            12.82            149                  889             1,426
```

```
Two Sheets (Cross-Sheet References)

Rows     DuckDB Time (s)    JS Time (s)    LO Time (s)    DuckDB Peak (MB)    JS Peak (MB)    LO Peak (MB)
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 10K        0.19               0.13            0.84             73                 106               233
100K        1.51               0.88            1.79             82                 172               376
500K        7.58               4.44            7.58            121                  491             1,186
```

## DuckDB Segment Timing Analysis

The DuckDB benchmark reports **segment-level timing** to identify bottlenecks:

| Segment | Description | 100K rows | 1M rows | % of Total (1M) |
|---------|-------------|-----------|---------|-----------------|
| **xlsx2csv** | XLSX → CSV conversion | 0.77s | 8.19s | 51% |
| **read_csv_auto** | CSV → DuckDB load | 0.04s | 0.10s | 0.6% |
| **formula_apply** | Formula evaluation | 0.01s | 0.02s | 0.1% |
| **xlsxwriter** | DuckDB → XLSX write | 0.74s | 7.62s | 48% |

**Key insight:** Formula evaluation scales exceptionally well. The bottleneck is streaming I/O (~99%), which is the cost of memory efficiency.

```
Example output:
{
  "rows": 100000,
  "segments": {
    "xlsx2csv": 0.771,
    "read_csv_auto": 0.041,
    "formula_apply": 0.008,
    "xlsxwriter": 0.743
  },
  "timeSeconds": 1.56,
  "peakTotalMB": 78.2,
  "usedMB": 23.9,
  "baselineMB": 54.3
}
```

## Quick Start (Docker/Podman)

```bash
# Build
podman build -t lo-vs-xlsx-benchmark .

# Run full benchmark
podman run --rm lo-vs-xlsx-benchmark

# Run individual tests
podman run --rm lo-vs-xlsx-benchmark python3 measure_lo.py 10000
podman run --rm lo-vs-xlsx-benchmark node measure_js.mjs 10000
podman run --rm lo-vs-xlsx-benchmark python3 measure_duckdb.py 10000
```

## Manual Setup

```bash
# Install dependencies
pip install openpyxl psutil duckdb xlsx2csv xlsxwriter
npm install xlsx xlsx-calc
# LibreOffice: brew install libreoffice (macOS) or apt install libreoffice (Linux)

# Run standard tests
for n in 10000 50000 100000 200000; do
    python3 measure_lo.py $n
    node measure_js.mjs $n
    python3 measure_duckdb.py $n
done

# Run 2-sheet tests
for n in 10000 100000 500000; do
    python3 measure_lo.py 2sheet_$n
    node measure_js.mjs 2sheet_$n
    python3 measure_duckdb.py 2sheet_$n
done
```

## Output Format

```json
{
  "rows": 10000,
  "segments": {
    "xlsx2csv": 0.095,
    "read_csv_auto": 0.044,
    "formula_apply": 0.015,
    "xlsxwriter": 0.074
  },
  "timeSeconds": 0.227,
  "peakTotalMB": 68.9,
  "usedMB": 13.1,
  "baselineMB": 55.9
}
```

- `rows` — Number of rows processed
- `segments` — Timing breakdown by execution phase (DuckDB only)
- `timeSeconds` — Total wall-clock time
- `peakTotalMB` — Peak RSS memory during operation
- `usedMB` — Net memory used for Excel work (baseline subtracted)
- `baselineMB` — Runtime overhead before work starts

## Benchmark Environment

Results obtained in containerized environment:

| Component | Version |
|-----------|---------|
| **Host Hardware** | Apple M2, 8 cores, 16 GB RAM |
| **Host OS** | macOS 26.2 (Darwin 25.2.0) |
| **Container** | Podman 5.7.1, 8 GB memory limit |
| **LibreOffice** | 7.4.7 (Debian bookworm) |
| **Node.js** | v20.20.0 |
| **Python** | 3.11.2 |
| **DuckDB** | 1.1.3 (with xlsx2csv 0.8.4, xlsxwriter 3.2.0) |

## Files

| File | Description |
|------|-------------|
| `measure_lo.py` | LibreOffice measurement (includes child processes) |
| `measure_js.mjs` | JS measurement with peak tracking |
| `measure_duckdb.py` | DuckDB measurement with segment timing (xlsx2csv → read_csv_auto → SQL → xlsxwriter) |
| `lib/formula_evaluator.py` | FormulaEvaluator library for complex formulas |
| `Dockerfile` | Container image |
| `docker-entrypoint.sh` | Automated benchmark script |
