import os
import yt_dlp

import traceback
import requests


from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.auth.dependencies import get_current_user

from app.models import Song, User, PlayHistory
from app.auth.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func



from app.schemas import SongCreate,SongResponse

router = APIRouter(
    prefix="/songs",
    tags=["Fetch"],
)

@router.get("/", response_model=list[SongResponse])
def get_songs(db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    songs = db.query(Song).order_by(Song.created_at.desc()).all()

    if not songs:
        raise HTTPException(status_code=404, detail="Song not found")

    return songs

@router.post("/play")
def add_play_history(
    youtube_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    song = db.query(Song).filter(
        Song.youtube_id == youtube_id
    ).first()

    if not song:
        raise HTTPException(
            status_code=404,
            detail="Song not found."
        )

    history = PlayHistory(
        user_id=current_user.id,
        youtube_id=youtube_id,
    )

    db.add(history)
    db.commit()

    return {
        "success": True,
    }
    

        