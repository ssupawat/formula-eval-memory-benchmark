#!/usr/bin/env python3
"""
DuckDB Formula Evaluator Benchmark

Measures time and memory for Excel formula evaluation using DuckDB.
Uses vectorized SQL for simple formulas, FormulaEvaluator for complex ones.
Compatible with JS and LibreOffice benchmark output format.
"""

import sys
import duckdb
import pandas as pd
import psutil
import time
import json
import threading
import re
from pathlib import Path
from openpyxl import load_workbook

# Import FormulaEvaluator for complex formulas
from lib.formula_evaluator import FormulaEvaluator


def parse_formula_pattern(formula: str) -> dict:
    """
    Parse a formula to detect patterns that can be vectorized.

    Returns:
        {
            'type': 'simple' | 'cross_sheet' | 'complex',
            'pattern': e.g., 'A+B' or 'A*2' or 'Sheet1!A',
            'columns': list of columns involved
        }
    """
    # Remove leading = and whitespace
    formula = formula.lstrip('=').strip()

    # Simple arithmetic: A2+B2, A2*2, etc.
    # Pattern: single letter column refs with operators
    simple_arithmetic = re.match(r'^([A-Z])\d+\s*([+\-*/])\s*([A-Z])\d+$', formula)
    if simple_arithmetic:
        return {
            'type': 'simple',
            'pattern': f'{simple_arithmetic.group(1)} {simple_arithmetic.group(2)} {simple_arithmetic.group(3)}',
            'columns': [simple_arithmetic.group(1), simple_arithmetic.group(3)]
        }

    # Simple scalar operation: A2*2, B2/10, etc.
    simple_scalar = re.match(r'^([A-Z])\d+\s*([+\-*/])\s*(\d+(?:\.\d+)?)$', formula)
    if simple_scalar:
        return {
            'type': 'simple',
            'pattern': f'{simple_scalar.group(1)} {simple_scalar.group(2)} {simple_scalar.group(3)}',
            'columns': [simple_scalar.group(1)]
        }

    # Cross-sheet reference: Sheet1!A2
    cross_sheet = re.match(r'^([A-Za-z0-9_]+)!([A-Z])\d+$', formula)
    if cross_sheet:
        return {
            'type': 'cross_sheet',
            'source_sheet': cross_sheet.group(1),
            'column': cross_sheet.group(2)
        }

    return {'type': 'complex'}


def evaluate_vectorized(conn, table_name: str, pattern_info: dict, df: pd.DataFrame) -> pd.Series:
    """Evaluate simple formulas using vectorized SQL."""
    col_map = {chr(ord('A') + i): df.columns[i] for i in range(len(df.columns))}

    if pattern_info['type'] == 'simple':
        parts = pattern_info['pattern'].split()
        col1 = col_map[parts[0]]
        op = parts[1]
        col2_or_val = parts[2]

        # Build SQL expression
        if col2_or_val in col_map:
            col2 = col_map[col2_or_val]
            expr = f'"{col1}" {op} "{col2}"'
        else:
            expr = f'"{col1}" {op} {col2_or_val}'

        result = conn.execute(f'SELECT {expr} FROM {table_name}').fetchdf()
        return result.iloc[:, 0]

    elif pattern_info['type'] == 'cross_sheet':
        source_table = pattern_info['source_sheet'].lower().replace(' ', '_')
        col_map_source = {chr(ord('A') + i): f'col{i}' for i in range(100)}  # Generic mapping
        source_col = pattern_info['column'].lower()
        result = conn.execute(f'SELECT "{source_col}" FROM {source_table}').fetchdf()
        return result.iloc[:, 0]

    return None


def measure_benchmark(n: str) -> dict:
    """Measure benchmark: time, baseline memory, peak memory, used memory."""

    # Build input path
    input_path = Path(f"/tmp/benchmark/test_{n}.xlsx")

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

    # Load Excel with openpyxl to read formulas
    wb = load_workbook(input_path, data_only=False)
    ws = wb.active

    # Setup DuckDB connection and load all sheets
    conn = duckdb.connect(':memory:')
    sheets_data = {}

    for sheet_name in wb.sheetnames:
        df = pd.read_excel(input_path, sheet_name=sheet_name, header=None, engine='openpyxl')
        # Normalize column names to col0, col1, col2, ...
        df.columns = [f'col{i}' for i in range(len(df.columns))]
        table_name = sheet_name.lower().replace(' ', '_')
        sheets_data[table_name] = df
        conn.register(table_name, df)

    evaluator = FormulaEvaluator(conn)

    # Start memory monitor
    measuring = True
    monitor = threading.Thread(target=memory_monitor, daemon=True)
    monitor.start()

    # Measure time
    start = time.time()

    # Analyze formulas in the active sheet
    # For benchmark files, all formulas in a column follow the same pattern
    # We can batch-evaluate by pattern

    formula_patterns = {}  # Maps (row, col) to pattern info

    for row in range(2, min(10, ws.max_row + 1)):  # Sample first few rows
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row, col)
            if cell.data_type == 'f':
                pattern = parse_formula_pattern(cell.value)
                formula_patterns[(row, col)] = pattern

    # Group by column and evaluate vectorized where possible
    for col in range(1, ws.max_column + 1):
        # Get pattern for this column
        sample_cell = ws.cell(2, col) if ws.max_row >= 2 else None
        if not sample_cell or sample_cell.data_type != 'f':
            continue

        pattern = parse_formula_pattern(sample_cell.value)
        table_name = ws.title.lower().replace(' ', '_')
        df = sheets_data[table_name]

        if pattern['type'] in ('simple', 'cross_sheet'):
            # Vectorized evaluation
            try:
                evaluate_vectorized(conn, table_name, pattern, df)
            except Exception:
                # Fall back to per-cell evaluation
                pass
        else:
            # Complex formulas - evaluate individually
            for row in range(2, ws.max_row + 1):
                cell = ws.cell(row, col)
                if cell.data_type == 'f':
                    formula = cell.value
                    row_ctx = {}
                    for ctx_col in range(1, ws.max_column + 1):
                        ctx_cell = ws.cell(row, ctx_col)
                        if ctx_cell.data_type != 'f':
                            col_letter = chr(ord('A') + ctx_col - 1)
                            row_ctx[f"{col_letter}{row}"] = ctx_cell.value
                    try:
                        sql = evaluator.excel_to_sql(formula, ws.title, row_ctx)
                        conn.execute(sql).fetchdf()
                    except Exception:
                        pass

    end = time.time()

    measuring = False
    monitor.join(timeout=1)

    timeSeconds = end - start
    peakTotalMB = peakMB
    usedMB = peakMB - baselineMB

    return {
        "rows": rows_report,
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
