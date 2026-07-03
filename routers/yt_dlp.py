import os
import yt_dlp

import traceback
import requests


from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.auth.dependencies import get_current_user
from app.models import User

from app.models import Song,DownloadHistory,PlayHistory
from app.auth.database import get_db
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/fetch",
    tags=["Fetch"],
)

BASE_DIR = "/opt/muzic/"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

 
def remove_file(path: str):
    """Delete file after response is sent."""
    if os.path.exists(path):
        os.remove(path)




def download_song(video_url: str, db: Session, current_user: User,playlist_id: str | None = None,playlist_title: str | None = None,):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "writethumbnail": True,
        "paths": {
            "home": DOWNLOAD_DIR,
        },
        "ignoreerrors": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {
                "key": "FFmpegThumbnailsConvertor",
                "format": "jpg",
            },
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        if info is None:
            return None
        

    mp3_path = os.path.join(DOWNLOAD_DIR, f"{info['id']}.mp3")

    if not os.path.exists(mp3_path):
        return None

    existing = db.query(Song).filter(
        Song.youtube_id == info["id"]
    ).first()

    if not existing:
        song = Song(
            youtube_id=info["id"],
            filename=info["title"],
        )
        
        history = DownloadHistory(
            user_id=current_user.id,
            youtube_id=info["id"],
            youtube_playlist_id=playlist_id,   # None for single videos
            playlist_title=playlist_title,     # None for single videos
        )
 
        db.add(song)
        db.commit()
        db.add(history)
        db.commit()

    return {
        "youtube_id": info["id"],
        "title": info["title"],
        "status": "exists" if existing else "downloaded",
    }
    
    
@router.post("/youtube")
def fetch_youtube_audio(
    url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        with yt_dlp.YoutubeDL({
            "quiet": True,
            "extract_flat": True,
        }) as ydl:
            info = ydl.extract_info(url, download=False)

        # Playlist
        if info.get("_type") == "playlist":
            results = []

            for entry in info.get("entries", []):
                if entry is None:
                    continue

                video_url = f"https://www.youtube.com/watch?v={entry['id']}"

                #result = download_song(video_url, db)
                result = download_song(
                    video_url,
                    db,
                    current_user,
                    info.get("id"),
                    info.get("title"),
                )
                if result is None:
                    raise HTTPException(
                        status_code=400,
                        detail="Unable to download this YouTube video."
                    )

                if result:
                    results.append(result)

            return {
                "success": True,
                "type": "playlist",
                "playlist": info.get("title"),
                "count": len(results),
                "songs": results,
            }

        # Single video
        #result = download_song(url, db)
        result = download_song(
            url,
            db,
            current_user,
        )

        return {
            "success": True,
            "type": "video",
            **result,
        }

    except Exception:
        traceback.print_exc()
        raise