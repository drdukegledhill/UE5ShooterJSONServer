# UE Telemetry Receiver (FastAPI)

A simple, production-ready FastAPI service for receiving telemetry from Unreal Engine.

Key features:
- POST /api/telemetry: accepts validated telemetry events
- Validation with Pydantic; invalid payloads return HTTP 400 with details
- Appends events to `data/data.jsonl` using file locking to prevent corruption
- Structured logging of (timestamp, IP, session_id, event_type)
- CORS enabled for all origins
- GET /health: returns `{ "status": "ok" }`

Quickstart:
1. Install dependencies (no virtualenv required)
   python -m pip install -r requirements.txt

2. Run the server
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

Optionally, make `run.sh` executable and run `./run.sh` to start the server.

Example POST (curl):

curl -X POST "http://127.0.0.1:8000/api/telemetry" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"abc","timestamp":"2026-01-12T12:34:56Z","event_type":"test","payload":{"k":"v"}}'

Notes:
- In production, run with multiple workers if needed. The implementation uses a file lock so multiple worker processes can safely append to `data/data.jsonl`.
- The service writes one JSON object per line (JSONL).

Docker (recommended for Synology)

- Build and run locally:

  docker build -t ue-telemetry:latest .
  docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name telemetry ue-telemetry:latest

- Or use docker-compose:

  docker-compose up -d --build

- Notes on volumes & locking ⚠️:
  - Mount `./data` as a bind volume (as above) so data is persisted on the Synology host.
  - Ensure the host volume is on a local filesystem (ext4, xfs); file locks may be unreliable on remote/NFS/SMB mounts and can risk data corruption.
  - Set proper ownership/permissions if necessary: `chown -R 1000:1000 ./data` (container runs as the unprivileged `telemetry` user).
