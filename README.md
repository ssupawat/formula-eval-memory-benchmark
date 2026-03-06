# Memory Benchmark: LibreOffice vs JS xlsx-calc

A comparison of peak memory usage between LibreOffice and JavaScript (SheetJS + xlsx-calc) for Excel formula evaluation.

## Key Finding

LibreOffice uses approximately **1.2-2.4x more peak memory** than JavaScript. The gap narrows at larger scales for single-sheet workbooks, but remains ~2x for multi-sheet workbooks.

```
Standard Tests (1 Sheet)

Rows     JS Peak (MB)    LibreOffice Peak (MB)    Ratio
────────────────────────────────────────────────────────
 10K        109               222                2.0x
 50K        158               223                1.4x
100K        219               283                1.3x
200K        339               405                1.2x
```

```
Max Rows (1 Sheet) - JS Only

Rows         JS Peak (MB)    Notes
───────────────────────────────────────────────────
1,048,576        875        LibreOffice OOM in container
                           (requires ~3GB when run locally)
```

```
Two Sheets (Cross-Sheet References)

Rows     JS Peak (MB)    LibreOffice Peak (MB)    Ratio
────────────────────────────────────────────────────────
 10K        108               233                2.1x
100K        189               376                2.0x
500K        494             1,186                2.4x
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
{"rows": 10000, "peakTotalMB": 261.4, "usedMB": 238.0, "baselineMB": 23.4}
```

- `peakTotalMB` — Peak RSS memory during operation
- `usedMB` — Net memory used for Excel work (baseline subtracted)
- `baselineMB` — Runtime overhead before work starts

## Benchmark Environment

Results obtained on the following system:

| Component | Version |
|-----------|---------|
| **Hardware** | Apple M2, 8 cores, 16 GB RAM |
| **OS** | macOS 26.2 (Darwin 25.2.0) |
| **LibreOffice** | 26.2.1.2 |
| **Node.js** | v25.6.0 |
| **Python** | 3.12.8 |
| **Container** | Podman 5.7.1 |

**Note:** Max rows (1M) LibreOffice test was run natively (outside container) due to memory requirements (~3GB).

## Files

| File | Description |
|------|-------------|
| `measure_lo.py` | LibreOffice measurement (includes child processes) |
| `measure_js.mjs` | JS measurement with peak tracking |
| `Dockerfile` | Container image |
| `docker-entrypoint.sh` | Automated benchmark script |
