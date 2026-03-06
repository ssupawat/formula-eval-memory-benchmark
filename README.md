# Memory Benchmark: LibreOffice vs JS xlsx-calc

A comparison of peak memory usage between LibreOffice and JavaScript (SheetJS + xlsx-calc) for Excel formula evaluation.

## Key Finding

LibreOffice uses approximately **2x more peak memory** than JavaScript.

```
Rows     JS Peak (MB)    LibreOffice Peak (MB)    Ratio
────────────────────────────────────────────────────────
 10K        105               234                2.2x
 50K        164               304                1.9x
100K        218               427                2.0x
200K        344               720                2.1x
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

# Run
for n in 10000 50000 100000 200000; do
    python3 measure_lo.py $n
    node measure_js.mjs $n
done
```

## Output Format

```json
{"rows": 10000, "peakTotalMB": 234.3, "usedMB": 210.9, "baselineMB": 23.4}
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
