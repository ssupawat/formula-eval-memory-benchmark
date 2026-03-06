import * as XLSX from "xlsx";
import XLSX_CALC from "xlsx-calc";
import { readFileSync, writeFileSync } from "fs";

const n = process.argv[2] || "10000";
const inputPath = `/tmp/benchmark/test_${n}.xlsx`;

// Extract row count for reporting
let rowsReport;
if (n === "max") {
  rowsReport = 1048576;
} else if (n.startsWith("2sheet_")) {
  rowsReport = parseInt(n.replace("2sheet_", ""));
} else {
  rowsReport = parseInt(n);
}

// Measure baseline before any operations (matches LibreOffice methodology)
const baseline = process.memoryUsage();

// Track peak RSS memory during operations (matches LibreOffice continuous monitoring)
let peakRss = baseline.rss;

function updatePeak() {
  const current = process.memoryUsage().rss;
  if (current > peakRss) peakRss = current;
}

// Start timing
const startTime = performance.now();

// Load and parse file
const buffer = readFileSync(inputPath);
updatePeak();

// Read workbook
const wb = XLSX.read(buffer);
updatePeak();

// Evaluate formulas
XLSX_CALC(wb);
updatePeak();

// Write output
const out = XLSX.write(wb, { type: "buffer", bookType: "xlsx" });
writeFileSync(`/tmp/out_js_mem_${n}.xlsx`, out);
updatePeak();

// Report in same format as LibreOffice for fair comparison
const peakTotalMB = (peakRss / 1024 / 1024).toFixed(1);
const baselineMB = (baseline.rss / 1024 / 1024).toFixed(1);
const usedMB = ((peakRss - baseline.rss) / 1024 / 1024).toFixed(1);
const elapsedSeconds = ((performance.now() - startTime) / 1000).toFixed(2);

console.log(JSON.stringify({
  rows: rowsReport,
  peakTotalMB: parseFloat(peakTotalMB),
  usedMB: parseFloat(usedMB),
  baselineMB: parseFloat(baselineMB),
  timeSeconds: parseFloat(elapsedSeconds),
}));
