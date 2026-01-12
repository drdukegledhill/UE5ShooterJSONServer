"""FastAPI application to receive telemetry from Unreal Engine.

Run instructions (development):
- Install requirements (no virtualenv required):
    python -m pip install -r requirements.txt

- Run with uvicorn (single process):
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

- Production (multiple workers):
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

- Optional: make `run.sh` executable and run `./run.sh` to start the server.

"""FastAPI application to receive telemetry from Unreal Engine.

# Run instructions (development):
# - Install requirements (no virtualenv required):
#     python -m pip install -r requirements.txt
# - Run with uvicorn (single process):
#     python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# - Production (multiple workers):
#     python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
# - Optional: make `run.sh` executable and run `./run.sh` to start the server.
# Endpoints:
# - POST /api/telemetry - accept a telemetry JSON (validated)
# - GET  /health        - simple health check
# Notes:
# - Payloads failing schema validation return HTTP 400 with clear error details.
# - Events are appended to `data/data.jsonl` with file locking to avoid corruption.
"""
from fastapi import Header

# Standard library imports
import os  # For file system operations
import json  # For JSON encoding/decoding
import logging  # For logging events
import datetime  # For timestamps
from typing import Dict, Any  # For type hints
from .storage import append_event, DATA_DIR


# FastAPI and related imports
from fastapi import FastAPI, Request, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import Body
from fastapi.encoders import jsonable_encoder
from fastapi import status
from fastapi import Header
from fastapi import Form
from fastapi import UploadFile, File
from fastapi import Response


# Local imports
from .models import TelemetryEvent  # Pydantic model for telemetry
from .storage import append_event, DATA_DIR  # File storage helpers
    CORSMiddleware,
    allow_origins=["*"],

# Setup logging for the API
logger = logging.getLogger("telemetry_api")  # Create logger
handler = logging.StreamHandler()  # Log to stderr
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")  # Log format
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)  # Set log level
async def startup_event():
    # Ensure data dir exists

# Create FastAPI app instance
app = FastAPI(title="UE Telemetry Receiver")
    logger.info(f"Data directory ready: {DATA_DIR}")

# Enable CORS for all origins (allow requests from anywhere)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):

# Startup event: ensure data directory exists
@app.on_event("startup")
async def startup_event():
    os.makedirs(DATA_DIR, exist_ok=True)  # Create data dir if missing
    logger.info(f"Data directory ready: {DATA_DIR}")  # Log startup
from fastapi import Request
from fastapi.responses import JSONResponse

# Shutdown event: log shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down telemetry API")

from fastapi import Depends

# Custom exception handler: return HTTP 400 for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": exc.errors()})
def parse_telemetry_form(
    session_id: str = Form(...),

# Helper to parse form-encoded telemetry data
def parse_telemetry_form(
    session_id: str = Form(...),
    event_type: str = Form(...),
    payload: str = Form("{}"),
    timestamp: Optional[str] = Form(None),
):
    import json
    try:
        payload_obj = json.loads(payload)  # Parse payload string as JSON
    except Exception:
        payload_obj = {}  # Default to empty dict if parsing fails
    return {
        "session_id": session_id,
        "event_type": event_type,
        "payload": payload_obj,
        "timestamp": timestamp,
    }
    payload: str = Form("{}"),

# Main telemetry endpoint: accepts JSON or form data
@app.post("/api/telemetry", status_code=201)
async def receive_telemetry(
    request: Request,
    content_type: str = Header(None),
    form_data: dict = Depends(parse_telemetry_form),
    event: Optional[TelemetryEvent] = None,
):
    """Receive a telemetry event, validate it, persist it, and log structured info."""
    import json
    from pydantic import ValidationError
    # Determine if request is JSON or form
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            body = await request.json()  # Parse JSON body
        except Exception:
            raise HTTPException(status_code=400, detail="Malformed JSON body.")
        # Fill timestamp if missing
        if "timestamp" not in body or not body["timestamp"]:
            body["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        try:
            event = TelemetryEvent(**body)  # Validate with Pydantic
        except ValidationError as exc:
            return JSONResponse(status_code=400, content={"detail": exc.errors()})
    else:
        # Use form_data
        data = form_data
        if not data.get("timestamp"):
            data["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
        try:
            event = TelemetryEvent(**data)  # Validate with Pydantic
        except ValidationError as exc:
            return JSONResponse(status_code=400, content={"detail": exc.errors()})

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
        append_event(event_dict)  # Write to file with locking
    except Exception as exc:
        logger.exception("Failed to persist event")
        raise HTTPException(status_code=500, detail="Failed to persist event")

    # Log structured info for audit/debug
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "ip": client_ip,
        "session_id": event.session_id,
        "event_type": event.event_type,
    }
    logger.info(json.dumps(log_entry, ensure_ascii=False))

    return {"status": "accepted"}
    except Exception as exc:
        logger.exception("Failed to persist event")

# Simple test/debug endpoint for UE5 Blueprints
@app.post("/api/test", status_code=200)
async def test_endpoint(request: Request):
    try:
        if request.headers.get("content-type", "").startswith("application/json"):
            data = await request.json()  # Parse JSON
        else:
            data = await request.form()  # Parse form
            data = dict(data)
    except Exception as exc:
        return JSONResponse(status_code=400, content={"detail": f"Error parsing input: {exc}"})
    return {"received": data}



# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}
    try:
        if request.headers.get("content-type", "").startswith("application/json"):

# Run the app directly (for development)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")
    except Exception as exc:
        return JSONResponse(status_code=400, content={"detail": f"Error parsing input: {exc}"})
    return {"received": data}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")