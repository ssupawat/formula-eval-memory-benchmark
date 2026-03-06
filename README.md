# Memory Benchmark: LibreOffice vs JS xlsx-calc

A comparison of peak memory usage and evaluation time between LibreOffice and JavaScript (SheetJS + xlsx-calc) for Excel formula evaluation.

## Key Findings

**Memory:** LibreOffice uses approximately **1.2-2.4x more peak memory** than JavaScript.

**Time:** JavaScript is **1.5-7x faster** for most workloads. LibreOffice is faster only for very large single-sheet files (1M+ rows).

```
Standard Tests (1 Sheet)

Rows     JS Time (s)    LO Time (s)    Time Ratio    JS Peak (MB)    LO Peak (MB)    Memory Ratio
───────────────────────────────────────────────────────────────────────────────────────────────────────
 10K        0.14            1.01           7.2x            109               222                2.0x
 50K        0.46            0.88           1.9x            158               223                1.4x
100K        0.91            1.45           1.6x            219               283                1.3x
200K        1.93            2.04           1.1x            339               405                1.2x
```

```
Max Rows (1 Sheet)

Rows         JS Time (s)    LO Time (s)    Time Ratio    JS Peak (MB)    LO Peak (MB)    Memory Ratio
────────────────────────────────────────────────────────────────────────────────────────────────────────
1,048,576       11.43            9.59           0.8x            874               1,425                1.6x
```

```
Two Sheets (Cross-Sheet References)

Rows     JS Time (s)    LO Time (s)    Time Ratio    JS Peak (MB)    LO Peak (MB)    Memory Ratio
────────────────────────────────────────────────────────────────────────────────────────────────────────
 10K        0.12            0.69           5.8x            108               233                2.1x
100K        0.78            1.81           2.3x            189               376                2.0x
500K        4.74            7.04           1.5x            494             1,186                2.4x
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
```

## Manual Setup

```bash
# Install dependencies
pip install openpyxl psutil
npm install xlsx xlsx-calc
# LibreOffice: brew install libreoffice (macOS) or apt install libreoffice (Linux)

# Run standard tests
for n in 10000 50000 100000 200000; do
    python3 measure_lo.py $n
    node measure_js.mjs $n
done

# Run 2-sheet tests
for n in 10000 100000 500000; do
    python3 measure_lo.py 2sheet_$n
    node measure_js.mjs 2sheet_$n
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

## Files

| File | Description |
|------|-------------|
| `measure_lo.py` | LibreOffice measurement (includes child processes) |
| `measure_js.mjs` | JS measurement with peak tracking |
| `Dockerfile` | Container image |
| `docker-entrypoint.sh` | Automated benchmark script |
