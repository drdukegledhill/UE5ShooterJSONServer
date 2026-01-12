def append_event(event: Dict[str, Any]) -> None:

"""
Small storage helper that appends JSON lines to data.jsonl using file-based locking.
Implementation notes:
  - Uses filelock.FileLock for cross-process locking (safe for multiple Uvicorn workers)
  - Ensures the data directory exists
  - Writes one JSON object per-line with an ISO8601 timestamp for `timestamp`
"""

# Standard library imports
from pathlib import Path  # For file paths
import json  # For JSON encoding
from typing import Dict, Any  # For type hints

# Third-party import
from filelock import FileLock  # For safe file locking

# Define base directory (project root)
BASE_DIR = Path(__file__).parent.parent
# Data directory for storing events
DATA_DIR = BASE_DIR / "data"
# Path to the JSONL file
DATA_FILE = DATA_DIR / "data.jsonl"
# Path to the lock file
LOCK_FILE = DATA_DIR / "data.jsonl.lock"

# Append a telemetry event to the JSONL file with file locking
def append_event(event: Dict[str, Any]) -> None:
    """
    Append event dict to the JSONL file with file locking.
    Args:
        event: A dict representing the event. `timestamp` should already be an ISO8601 string.
    Raises:
        Any IO exception (will bubble up to be handled by caller).
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)  # Ensure data dir exists

    lock = FileLock(str(LOCK_FILE))  # Acquire file lock
    with lock:
        # Open in append mode and write a single JSON object per line
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")  # Write event as JSONL
