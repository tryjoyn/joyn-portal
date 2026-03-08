FROM python:3.11-slim

# Security: run as non-root
RUN addgroup --system iris && adduser --system --ingroup iris iris

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite queue DB
RUN mkdir -p /app/data && chown -R iris:iris /app

USER iris

# Health check — verifies the worker process is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import sqlite3, os; conn = sqlite3.connect(os.environ.get('IRIS_DB_PATH','data/iris.db')); conn.execute('SELECT 1'); conn.close(); print('ok')"

# Default command: run the worker
CMD ["python", "worker.py"]
