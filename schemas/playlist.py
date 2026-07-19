from pydantic import BaseModel

class PlaylistRequest(BaseModel):
    video_url: str