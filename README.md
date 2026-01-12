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

---

## Integrating with Unreal Engine 5 Blueprints

You can send telemetry from UE5 Blueprints to this API using the built-in HTTP request nodes. The API accepts both JSON and form-encoded data, making integration easy.

### Step-by-step: Sending Telemetry from Blueprints

1. **Add HTTP Request Node**
   - In your Blueprint (e.g., Level or Actor Blueprint), right-click and search for `Construct Http Request`.
   - Use the `Construct Http Request` node (from the HTTP module).

2. **Set up the Request**
   - Add a `Set URL` node and set it to your API endpoint, e.g.:
     - `http://YOUR_SERVER_IP:8000/api/telemetry`
   - Add a `Set Verb` node and set it to `POST`.
   - Add a `Set Header` node:
     - Key: `Content-Type`
     - Value: `application/json`

3. **Build the JSON Payload**
   - Use Blueprint nodes to build a JSON string, e.g.:
     ```json
     {
       "session_id": "test-session",
       "event_type": "jump",
       "payload": { "height": 123 }
     }
     ```
   - (You can omit `timestamp`—the server will auto-fill it if missing.)
   - Use `Set Content As String` to set the request body to your JSON string.

4. **Send the Request**
   - Call `Process Request` to send.

5. **(Optional) Handle the Response**
   - Bind the `On Process Request Complete` event to handle success/failure.

#### Example Node Flow

1. **Event (e.g., On Button Pressed)**
2. → `Construct Http Request`
3. → `Set URL` (`http://your-server:8000/api/telemetry`)
4. → `Set Verb` (`POST`)
5. → `Set Header` (`Content-Type: application/json`)
6. → `Set Content As String` (your JSON)
7. → `Process Request`
8. → `On Process Request Complete` (handle response)

#### Tips
- You can use the `/api/test` endpoint to debug and see exactly what your Blueprint sends.
- If you want to use form data instead of JSON, set `Content-Type: application/x-www-form-urlencoded` and use `Set Content As String` with a string like:
  ```
  session_id=test-session&event_type=jump&payload={"height":123}
  ```
- The API will return HTTP 400 with error details if required fields are missing or the payload is invalid.
- CORS is enabled for all origins, so you can POST from any client.

---
