from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any


class TelemetryEvent(BaseModel):
    """Pydantic model for incoming telemetry events.

    Fields:
    - session_id: non-empty string
    - timestamp: ISO8601 datetime string (parsed to datetime)
    - event_type: non-empty string
    - payload: free-form object (must be a JSON object / mapping)
    """

    session_id: str = Field(..., min_length=1)
    timestamp: datetime
    event_type: str = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "session_id": "abc123",
                "timestamp": "2026-01-12T12:34:56Z",
                "event_type": "player_jump",
                "payload": {"height": 2.3, "location": {"x": 12, "y": 5}}
            }
        }