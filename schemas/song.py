from datetime import datetime
from pydantic import BaseModel

class SongCreate(BaseModel):
    youtube_id: str
    filename: str

class SongResponse(BaseModel):
    youtube_id: str
    filename: str
    created_at: datetime

    model_config = {
        "from_attributes": True  # Pydantic v2
    }
    