"""Small storage helper that appends JSON lines to data.jsonl using file-based locking.

Implementation notes:
- Uses `filelock.FileLock` for cross-process locking (safe for multiple Uvicorn workers)
- Ensures the data directory exists
- Writes one JSON object per-line with an ISO8601 timestamp for `timestamp`
"""
from pathlib import Path
import json
from typing import Dict, Any

from filelock import FileLock

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "data.jsonl"
LOCK_FILE = DATA_DIR / "data.jsonl.lock"


def append_event(event: Dict[str, Any]) -> None:
    """Append event dict to the JSONL file with file locking.

    Args:
        event: A dict representing the event. `timestamp` should already be
               an ISO8601 string.

    Raises:
        Any IO exception (will bubble up to be handled by caller).
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    lock = FileLock(str(LOCK_FILE))
    with lock:
        # Open in append mode and write a single JSON object per line
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
