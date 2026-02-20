FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc && \
    rm -rf /var/lib/apt/lists/*

# Python deps (lightweight, auth-only)
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Copy app source
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Cloud Run sets PORT env var
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main_cloud:app --host 0.0.0.0 --port $PORT"]
