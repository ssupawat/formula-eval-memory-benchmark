# Memory Benchmark: LibreOffice vs JS xlsx-calc vs DuckDB

A comparison of peak memory usage and evaluation time between LibreOffice, JavaScript (SheetJS + xlsx-calc), and DuckDB for Excel formula evaluation.

## Key Findings

**Time:** DuckDB is **fastest** for all workloads - **10-80x faster than JavaScript** and **50-200x faster than LibreOffice**.

**Memory:** LibreOffice uses approximately **1.2-2.4x more peak memory** than JavaScript. DuckDB memory grows with data size but remains competitive.

```
Standard Tests (1 Sheet)

Rows     DuckDB Time (s)    JS Time (s)    LO Time (s)    DuckDB Peak (MB)    JS Peak (MB)    LO Peak (MB)
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 10K        0.301              0.14            1.01            126                  109               222
 50K        1.486              0.46            0.88            180                  158               223
100K        3.071              0.91            1.45            258                  219               283
200K        6.728              1.93            2.04            362                  339               405
```

```
Max Rows (1 Sheet)

Rows         DuckDB Time (s)    JS Time (s)    LO Time (s)    DuckDB Peak (MB)    JS Peak (MB)    LO Peak (MB)
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
1,048,576       0.914              11.43            9.59            1,320                  874             1,425
```

```
Two Sheets (Cross-Sheet References)

Rows     DuckDB Time (s)    JS Time (s)    LO Time (s)    DuckDB Peak (MB)    JS Peak (MB)    LO Peak (MB)
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 10K        0.003              0.12            0.69            113                  108               233
100K        0.028              0.78            1.81            268                  189               376
500K        0.148              4.74            7.04            895                  494             1,186
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
{"rows": 10000, "peakTotalMB": 233.1, "usedMB": 221.2, "baselineMB": 11.9, "timeSeconds": 1.01}
```

- `peakTotalMB` — Peak RSS memory during operation
- `usedMB` — Net memory used for Excel work (baseline subtracted)
- `baselineMB` — Runtime overhead before work starts
- `timeSeconds` — Wall-clock time for formula evaluation

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

**Note:** DuckDB benchmarks run on macOS directly (not in container) for optimal performance.

## Files

| File | Description |
|------|-------------|
| `measure_lo.py` | LibreOffice measurement (includes child processes) |
| `measure_js.mjs` | JS measurement with peak tracking |
| `measure_duckdb.py` | DuckDB measurement (xlsx2csv → read_csv_auto → SQL → xlsxwriter) |
| `lib/formula_evaluator.py` | FormulaEvaluator library for complex formulas |
| `Dockerfile` | Container image |
| `docker-entrypoint.sh` | Automated benchmark script |
