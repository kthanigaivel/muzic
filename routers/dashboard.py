from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func,desc
import os

from app.auth.dependencies import get_current_user
from app.models import User

from app.auth.database import get_db
from sqlalchemy.orm import Session

from app.models import (
    User,
    Song,
    Favorite,
    DownloadHistory,
    PlayHistory,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)



@router.get("/dashboard")
def dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    total_users = db.query(func.count(User.id)).scalar()

    total_songs = db.query(func.count(Song.youtube_id)).scalar()

    total_downloads = db.query(
        func.count(DownloadHistory.id)
    ).scalar()

    total_plays = db.query(
        func.count(PlayHistory.id)
    ).scalar()

    recent_downloads = (
        db.query(
            DownloadHistory,
            User.username,
            Song.filename,
        )
        .join(User, DownloadHistory.user_id == User.id)
        .join(Song, DownloadHistory.youtube_id == Song.youtube_id)
        .order_by(DownloadHistory.downloaded_at.desc())
        .limit(20)
        .all()
    )

    recent_plays = (
        db.query(
            PlayHistory,
            User.username,
            Song.filename,
        )
        .join(User, PlayHistory.user_id == User.id)
        .join(Song, PlayHistory.youtube_id == Song.youtube_id)
        .order_by(PlayHistory.played_at.desc())
        .limit(20)
        .all()
    )
    top_downloads = (
        db.query(
            Song.filename,
            Song.youtube_id,
            func.count(DownloadHistory.id).label("count"),
        )
        .join(
            DownloadHistory,
            Song.youtube_id == DownloadHistory.youtube_id,
        )
        .group_by(
            Song.youtube_id,
            Song.filename,
        )
        .order_by(func.count(DownloadHistory.id).desc())
        .limit(10)
        .all()
    )

    top_plays = (
        db.query(
            Song.filename,
            Song.youtube_id,
            func.count(PlayHistory.id).label("count"),
        )
        .join(
            PlayHistory,
            Song.youtube_id == PlayHistory.youtube_id,
        )
        .group_by(
            Song.youtube_id,
            Song.filename,
        )
        .order_by(func.count(PlayHistory.id).desc())
        .limit(10)
        .all()
    )

    return {

        "overview": {
            "users": total_users,
            "songs": total_songs,
            "downloads": total_downloads,
            "plays": total_plays,
        },

        "recent_downloads": [
            {
                "username": username,
                "youtube_id": history.youtube_id,
                "title": filename,
                "playlist": history.playlist_title,
                "downloaded_at": history.downloaded_at,
            }
            for history, username, filename in recent_downloads
        ],

        "recent_plays": [
            {
                "username": username,
                "youtube_id": history.youtube_id,
                "title": filename,
                "played_at": history.played_at,
            }
            for history, username, filename in recent_plays
        ],

        "top_downloads": [
            {
                "youtube_id": x.youtube_id,
                "title": x.filename,
                "count": x.count,
            }
            for x in top_downloads
        ],

        "top_plays": [
            {
                "youtube_id": x.youtube_id,
                "title": x.filename,
                "count": x.count,
            }
            for x in top_plays
        ],
    }