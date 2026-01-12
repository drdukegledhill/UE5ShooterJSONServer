FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install curl for HEALTHCHECK and keep image small
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Create unprivileged user and ensure data dir exists
RUN adduser --disabled-password --gecos "" telemetry || true \
    && mkdir -p /app/data \
    && chown -R telemetry:telemetry /app/data /app

USER telemetry

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
