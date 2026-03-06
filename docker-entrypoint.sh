#!/bin/bash
# Helper script to run the benchmark in Docker

set -e

# Generate test files if they don't exist
python3 -c "
from openpyxl import Workbook
from pathlib import Path

def generate_workbook(n):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Sheet1'

    # Header
    ws['A1'] = 'A'
    ws['B1'] = 'B'
    ws['C1'] = 'C = A + B'

    # Data with formulas
    for i in range(2, n + 2):
        ws[f'A{i}'] = i
        ws[f'B{i}'] = i * 2
        ws[f'C{i}'] = f'=A{i}+B{i}'

    Path(f'/tmp/benchmark/test_{n}.xlsx').parent.mkdir(parents=True, exist_ok=True)
    wb.save(f'/tmp/benchmark/test_{n}.xlsx')
    print(f'Generated test_{n}.xlsx')

# Generate test files for different sizes
for n in [10000, 50000, 100000, 200000]:
    generate_workbook(n)
"

echo "Generated test files"

# Run LibreOffice benchmark
echo "=== LibreOffice Benchmark ==="
for n in 10000 50000 100000 200000; do
    echo "Running LibreOffice benchmark with $n rows..."
    python3 measure_lo.py $n
done

# Run JS benchmark
echo "=== JS Benchmark ==="
for n in 10000 50000 100000 200000; do
    echo "Running JS benchmark with $n rows..."
    node measure_js.mjs $n
done
