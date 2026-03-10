#!/usr/bin/env python3
"""
DuckDB Formula Evaluator Benchmark

Measures time and memory for Excel formula evaluation using DuckDB.
Uses xlsx2csv library for CSV conversion, DuckDB read_csv_auto for loading,
and xlsxwriter for writing output.

This simplified version reads the XLSX file ONCE with xlsx2csv, then applies
a known formula pattern using FormulaEvaluator's apply_formula_to_column().

Compatible with JS and LibreOffice benchmark output format.
"""

import sys
import duckdb
import psutil
import time
import json
import threading
import os
from pathlib import Path
from xlsx2csv import Xlsx2csv
import xlsxwriter
import tempfile

# Import FormulaEvaluator for formula application
from lib.formula_evaluator import FormulaEvaluator


def measure_benchmark(n: str) -> dict:
    """Measure benchmark: time, baseline memory, peak memory, used memory."""

    # Build paths
    input_path = Path(f"/tmp/benchmark/test_{n}.xlsx")
    output_path = Path(f"/tmp/out_duckdb_{n}.xlsx")

    # Extract row count for reporting
    if n == "max":
        rows_report = 1048576
    elif n.startswith("2sheet_"):
        rows_report = int(n.replace("2sheet_", ""))
    else:
        rows_report = int(n)

    process = psutil.Process()

    # Measure baseline
    baselineMB = process.memory_info().rss / 1024 / 1024
    peakMB = baselineMB

    measuring = False

    def memory_monitor():
        nonlocal peakMB
        while measuring:
            peakMB = max(peakMB, process.memory_info().rss / 1024 / 1024)
            time.sleep(0.01)

    # Start memory monitor BEFORE any work
    measuring = True
    monitor = threading.Thread(target=memory_monitor, daemon=True)
    monitor.start()

    # Measure time
    start = time.time()
    segments = {}

    # Segment 1: xlsx2csv
    step_start = time.time()
    # Step 1: Convert XLSX to CSV using xlsx2csv
    temp_dir = tempfile.mkdtemp()
    csv_files = {}

    # Determine sheet names based on test type (known structure)
    if n.startswith("2sheet_"):
        sheet_names = ["Sheet1", "Sheet2"]
    else:
        sheet_names = ["Sheet1"]

    for sheet_name in sheet_names:
        csv_path = os.path.join(temp_dir, f"{sheet_name}.csv")
        converter = Xlsx2csv(input_path, sheetname=sheet_name)
        converter.convert(csv_path)
        csv_files[sheet_name] = csv_path
    segments['xlsx2csv'] = round(time.time() - step_start, 3)

    # Segment 2: read_csv_auto
    step_start = time.time()
    # Step 2: Load CSVs into DuckDB using read_csv_auto
    conn = duckdb.connect(':memory:')

    for sheet_name, csv_path in csv_files.items():
        table_name = sheet_name.lower().replace(' ', '_')

        # Load CSV and cast columns to DOUBLE (xlsx2csv outputs strings)
        result = conn.execute(f"SELECT * FROM read_csv_auto('{csv_path}', header=False)")
        columns = result.description

        if n.startswith("2sheet_") and sheet_name == "Sheet2":
            # 2sheet test: Sheet2 CSV only has 1 column due to empty formula cells
            # We need to create the table with 2 columns and will populate it later
            col_list = ', '.join([f'TRY_CAST("{col[0]}" AS DOUBLE) AS "{col[0]}"' for col in columns])
            conn.execute(f"CREATE TABLE {table_name} AS SELECT {col_list}, NULL AS \"column1\" FROM read_csv_auto('{csv_path}', header=False)")
        else:
            col_list = ', '.join([f'TRY_CAST("{col[0]}" AS DOUBLE) AS "{col[0]}"' for col in columns])
            conn.execute(f"CREATE TABLE {table_name} AS SELECT {col_list} FROM read_csv_auto('{csv_path}', header=False)")
    segments['read_csv_auto'] = round(time.time() - step_start, 3)

    # Segment 3: formula_apply
    step_start = time.time()
    # Step 3: Apply formulas using FormulaEvaluator
    evaluator = FormulaEvaluator(conn)

    if n.startswith("2sheet_"):
        # 2sheet test: Sheet2 has cross-sheet reference and formula
        # Sheet2 column A: =Sheet1!A2 (cross-sheet reference)
        # Sheet2 column B: =A2*2 (formula on Sheet2's column A)
        evaluator.apply_formula_to_column('=Sheet1!A2', 'Sheet2', 'column0')
        evaluator.apply_formula_to_column('=A2*2', 'Sheet2', 'column1')
    else:
        # Standard test: Compute C = A + B
        # Column C (column2) = A (column0) + B (column1)
        evaluator.apply_formula_to_column('=A2+B2', 'Sheet1', 'column2')
    segments['formula_apply'] = round(time.time() - step_start, 3)

    # Segment 4: xlsxwriter
    step_start = time.time()
    # Step 4: Write results to XLSX using xlsxwriter with constant memory mode
    workbook = xlsxwriter.Workbook(output_path, {'constant_memory': True})

    for sheet_name in csv_files.keys():
        table_name = sheet_name.lower().replace(' ', '_')

        # Write to worksheet
        worksheet = workbook.add_worksheet(sheet_name)

        # Stream data from DuckDB in chunks to avoid loading all into memory
        result = conn.execute(f"SELECT * FROM {table_name}")

        # Fetch and write in batches
        row_idx = 0
        while True:
            # Fetch a batch of rows as list of tuples
            batch = result.fetchmany(10000)
            if not batch:
                break

            for row_data in batch:
                for col_idx, value in enumerate(row_data):
                    worksheet.write(row_idx, col_idx, value)
                row_idx += 1

    workbook.close()
    segments['xlsxwriter'] = round(time.time() - step_start, 3)

    # Cleanup
    end = time.time()
    measuring = False
    monitor.join(timeout=1)

    # Clean up temp files
    for csv_path in csv_files.values():
        if os.path.exists(csv_path):
            os.remove(csv_path)
    os.rmdir(temp_dir)

    timeSeconds = end - start
    peakTotalMB = peakMB
    usedMB = peakMB - baselineMB

    return {
        "rows": rows_report,
        "segments": segments,
        "peakTotalMB": round(peakTotalMB, 1),
        "usedMB": round(usedMB, 1),
        "baselineMB": round(baselineMB, 1),
        "timeSeconds": round(timeSeconds, 3)
    }


def main():
    n = sys.argv[1] if len(sys.argv) > 1 else "10000"
    result = measure_benchmark(n)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
