# Docker Instructions

## Build the Docker Image

```bash
docker build -t lo-vs-xlsx-benchmark .
```

## Run the Full Benchmark

```bash
docker run --rm lo-vs-xlsx-benchmark
```

## Run Individual Benchmarks

### LibreOffice only (10K rows)
```bash
docker run --rm lo-vs-xlsx-benchmark python3 measure_lo.py 10000
```

### JS only (10K rows)
```bash
docker run --rm lo-vs-xlsx-benchmark node measure_js.mjs 10000
```

## Run with Different Row Counts

```bash
docker run --rm lo-vs-xlsx-benchmark python3 measure_lo.py 50000
docker run --rm lo-vs-xlsx-benchmark node measure_js.mjs 50000
```

## Interactive Shell

```bash
docker run --rm -it lo-vs-xlsx-benchmark bash
```

Then inside the container:
```bash
python3 measure_lo.py 100000
node measure_js.mjs 100000
```
