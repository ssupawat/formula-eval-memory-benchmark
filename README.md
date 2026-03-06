# Memory Benchmark: LibreOffice vs JS xlsx-calc

A comparison of peak memory usage between LibreOffice and JavaScript (SheetJS + xlsx-calc) for Excel formula evaluation.

## Key Finding

LibreOffice uses approximately **2-4x more peak memory** than JavaScript, with the gap widening at scale and with multi-sheet workbooks.

```
Standard Tests (1 Sheet)

Rows     JS Peak (MB)    LibreOffice Peak (MB)    Ratio
────────────────────────────────────────────────────────
 10K        106               261                2.5x
 50K        162               315                1.9x
100K        216               427                2.0x
200K        339               724                2.1x
```

```
Max Rows (1 Sheet)

Rows         JS Peak (MB)    LibreOffice Peak (MB)    Ratio
────────────────────────────────────────────────────────────
1,048,576        873               2,931                3.4x
```

```
Two Sheets (Cross-Sheet References)

Rows     JS Peak (MB)    LibreOffice Peak (MB)    Ratio
────────────────────────────────────────────────────────
 10K        108               260                2.4x
100K        169               529                3.1x
500K        452             1,953                4.3x
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

## Files

| File | Description |
|------|-------------|
| `measure_lo.py` | LibreOffice measurement (includes child processes) |
| `measure_js.mjs` | JS measurement with peak tracking |
| `Dockerfile` | Container image |
| `docker-entrypoint.sh` | Automated benchmark script |
