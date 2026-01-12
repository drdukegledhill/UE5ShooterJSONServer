#!/usr/bin/env bash
# Simple runner for the telemetry service without creating a virtualenv.
# Make executable with `chmod +x run.sh` then run `./run.sh`.

set -euo pipefail

# Use python -m uvicorn to ensure the module lookup works even if uvicorn is installed
# in the user site-packages or system Python.
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
