# Memory Benchmark: LibreOffice vs JS xlsx-calc vs DuckDB

A comparison of peak memory usage and evaluation time between LibreOffice, JavaScript (SheetJS + xlsx-calc), and DuckDB for Excel formula evaluation.

## Key Findings

**Time:** DuckDB's **formula evaluation is extremely fast** - under 0.01s even for 1M rows. However, **streaming I/O dominates** the runtime.

**Memory:** DuckDB uses **5-10x less memory** than JS and **10-20x less** than LibreOffice at scale.

```
Standard Tests (1 Sheet)

Rows     DuckDB Time (s)    JS Time (s)    LO Time (s)    DuckDB Peak (MB)    JS Peak (MB)    LO Peak (MB)
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 10K        0.215              0.14            1.01             63                 109               222
 50K        0.918              0.46            0.88             69                 158               223
100K        1.709              0.91            1.45             70                 219               283
200K        3.349              1.93            2.04             75                 339               405
```

```
Max Rows (1 Sheet)

Rows         DuckDB Time (s)    JS Time (s)    LO Time (s)    DuckDB Peak (MB)    JS Peak (MB)    LO Peak (MB)
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
1,048,576       12.30             11.43            9.59            109                  874             1,425
```

```
Two Sheets (Cross-Sheet References)

Rows     DuckDB Time (s)    JS Time (s)    LO Time (s)    DuckDB Peak (MB)    JS Peak (MB)    LO Peak (MB)
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 10K        0.250              0.12            0.69             69                 108               233
100K        1.804              0.78            1.81             76                 189               376
500K        9.028              4.74            7.04            112                  494             1,186
```

## DuckDB Segment Timing Analysis

The DuckDB benchmark now reports **segment-level timing** to identify bottlenecks:

| Segment | Description | 100K rows | 1M rows | % of Total (1M) |
|---------|-------------|-----------|---------|-----------------|
| **xlsx2csv** | XLSX → CSV conversion | 0.79s | 6.15s | 50% |
| **read_csv_auto** | CSV → DuckDB load | 0.04s | 0.08s | 0.7% |
| **formula_apply** | Formula evaluation | 0.01s | 0.01s | 0.1% |
| **xlsxwriter** | DuckDB → XLSX write | 0.87s | 6.06s | 49% |

**Key insight:** Formula evaluation scales exceptionally well (0.007s → 0.01s from 10K → 1M rows). The bottleneck is streaming I/O (xlsx2csv + xlsxwriter = ~99%), which is the cost of memory efficiency.

```
Example output:
{
  "rows": 100000,
  "segments": {
    "xlsx2csv": 0.79,
    "read_csv_auto": 0.04,
    "formula_apply": 0.01,
    "xlsxwriter": 0.87
  },
  "timeSeconds": 1.71,
  "peakTotalMB": 70.3,
  "usedMB": 27.3,
  "baselineMB": 43.0
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
    "xlsx2csv": 0.082,
    "read_csv_auto": 0.033,
    "formula_apply": 0.009,
    "xlsxwriter": 0.090
  },
  "timeSeconds": 0.215,
  "peakTotalMB": 63.1,
  "usedMB": 19.7,
  "baselineMB": 43.4
}
```

- `rows` — Number of rows processed
- `segments` — Timing breakdown by execution phase (DuckDB only)
- `timeSeconds` — Total wall-clock time
- `peakTotalMB` — Peak RSS memory during operation
- `usedMB` — Net memory used for Excel work (baseline subtracted)
- `baselineMB` — Runtime overhead before work starts

## Benchmark Environment

Results obtained on macOS directly (not containerized):

| Component | Version |
|-----------|---------|
| **Host Hardware** | Apple M2, 8 cores, 16 GB RAM |
| **Host OS** | macOS 26.2 (Darwin 25.2.0) |
| **Python** | 3.13.1 |
| **DuckDB** | 1.1.3 (with xlsx2csv 0.8.4, xlsxwriter 3.2.0) |

**Note:** JS and LibreOffice results from previous container runs for comparison.

## Files

| File | Description |
|------|-------------|
| `measure_lo.py` | LibreOffice measurement (includes child processes) |
| `measure_js.mjs` | JS measurement with peak tracking |
| `measure_duckdb.py` | DuckDB measurement with segment timing (xlsx2csv → read_csv_auto → SQL → xlsxwriter) |
| `lib/formula_evaluator.py` | FormulaEvaluator library for complex formulas |
| `Dockerfile` | Container image |
| `docker-entrypoint.sh` | Automated benchmark script |
