FROM python:3.11-slim

WORKDIR /app

# Python deps (lightweight)
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Copy only the standalone server
COPY server.py .

# Create data directory for SQLite
RUN mkdir -p /tmp/data

# Cloud Run sets PORT env var
ENV PORT=8080
ENV GAIM_DATA_DIR=/tmp/data
EXPOSE 8080

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port $PORT"]
