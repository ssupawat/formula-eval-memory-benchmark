FROM node:20-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --break-system-packages openpyxl psutil duckdb pandas numexpr xlsx2csv xlsxwriter

# Copy benchmark files first (for package.json)
COPY measure_lo.py /app/
COPY measure_js.mjs /app/
COPY measure_duckdb.py /app/
COPY lib/formula_evaluator.py /app/lib/formula_evaluator.py
COPY docker-entrypoint.sh /app/

# Create package.json and install Node dependencies locally
WORKDIR /app
RUN echo '{"type":"module","dependencies":{"xlsx":"*","xlsx-calc":"*"}}' > package.json && \
    npm install

# Create benchmark directory
RUN mkdir -p /tmp/benchmark

# Make entrypoint executable
RUN chmod +x /app/docker-entrypoint.sh

# Set working directory
WORKDIR /app

# Run the full benchmark by default
CMD ["/app/docker-entrypoint.sh"]
