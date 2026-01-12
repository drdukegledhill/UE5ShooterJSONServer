"""FastAPI application to receive telemetry from Unreal Engine.

Run instructions (development):
- Install requirements (no virtualenv required):
    python -m pip install -r requirements.txt

- Run with uvicorn (single process):
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

- Production (multiple workers):
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

- Optional: make `run.sh` executable and run `./run.sh` to start the server.

Endpoints:
- POST /api/telemetry - accept a telemetry JSON (validated)
- GET  /health        - simple health check

Notes:
- Payloads failing schema validation return HTTP 400 with clear error details.
- Events are appended to `data/data.jsonl` with file locking to avoid corruption.
"""
import os
import json
import logging
import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from .models import TelemetryEvent
from .storage import append_event, DATA_DIR


# Setup logging
logger = logging.getLogger("telemetry_api")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


app = FastAPI(title="UE Telemetry Receiver")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Ensure data dir exists
    os.makedirs(DATA_DIR, exist_ok=True)
    logger.info(f"Data directory ready: {DATA_DIR}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down telemetry API")


# Return HTTP 400 for validation errors with clear details
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # exc.errors() is a list of validation problems
    return JSONResponse(status_code=400, content={"detail": exc.errors()})


@app.post("/api/telemetry", status_code=201)
async def receive_telemetry(event: TelemetryEvent, request: Request):
    """Receive a telemetry event, validate it, persist it, and log structured info."""

    # Get real client IP (support X-Forwarded-For if behind a proxy)
    raw_xff = request.headers.get("x-forwarded-for")
    if raw_xff:
        client_ip = raw_xff.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    # Prepare dict to persist; ensure timestamp is ISO8601 string
    event_dict: Dict[str, Any] = event.dict()
    # Pydantic parsed timestamp to datetime; convert back to ISO
    event_dict["timestamp"] = event.timestamp.isoformat()

    try:
        append_event(event_dict)
    except Exception as exc:
        logger.exception("Failed to persist event")
        raise HTTPException(status_code=500, detail="Failed to persist event")

    # Log structured info
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "ip": client_ip,
        "session_id": event.session_id,
        "event_type": event.event_type,
    }
    logger.info(json.dumps(log_entry, ensure_ascii=False))

    return {"status": "accepted"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")