
# Pydantic and typing imports
from pydantic import BaseModel, Field  # For data validation
from datetime import datetime  # For timestamp parsing
from typing import Dict, Any  # For type hints



# Pydantic model for incoming telemetry events
class TelemetryEvent(BaseModel):
    """
    Telemetry event schema for validation.
    Fields:
      - session_id: non-empty string (required)
      - timestamp: ISO8601 datetime string (optional, auto-filled if missing)
      - event_type: non-empty string (required)
      - payload: free-form object (dict, can be empty)
    """
    session_id: str = Field(..., min_length=1)  # Unique session identifier
    timestamp: datetime = None  # Optional timestamp, will be set to now if missing
    event_type: str = Field(..., min_length=1)  # Event type string
    payload: Dict[str, Any] = Field(default_factory=dict)  # Free-form payload

    class Config:
        schema_extra = {
            "example": {
                "session_id": "abc123",
                "timestamp": "2026-01-12T12:34:56Z",
                "event_type": "player_jump",
                "payload": {"height": 2.3, "location": {"x": 12, "y": 5}}
            }
        }