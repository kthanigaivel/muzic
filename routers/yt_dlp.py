import os
import yt_dlp

import traceback
import requests


from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.models import User

from app.models import Song,DownloadHistory
from app.auth.database import get_db
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/fetch",
    tags=["Fetch"],
)

BASE_DIR = "/opt/muzic/"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_song(
    video_url: str,
    db: Session,
    current_user: User,
    playlist_id: str | None = None,
    playlist_title: str | None = None,
):
    # First get metadata only
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(video_url, download=False)

    if info is None:
        return None

    youtube_id = info["id"]
    title = info["title"]

    mp3_path = os.path.join(DOWNLOAD_DIR, f"{youtube_id}.mp3")
    thumbnail_path = os.path.join(DOWNLOAD_DIR, f"{youtube_id}.jpg")

    existing = db.query(Song).filter(
        Song.youtube_id == youtube_id
    ).first()

    # Already downloaded -> don't download again
    if existing and os.path.exists(mp3_path):

        if not os.path.exists(thumbnail_path):
            url = f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"
            r = requests.get(url, timeout=10)
            if r.ok:
                with open(thumbnail_path, "wb") as f:
                    f.write(r.content)

        try:
            history = DownloadHistory(
                user_id=current_user.id,
                youtube_id=youtube_id,
                youtube_playlist_id=playlist_id,
                playlist_title=playlist_title,
            )

            db.add(history)
            db.commit()

        except Exception:
            db.rollback()
            raise

        return {
            "youtube_id": youtube_id,
            "title": title,
            "thumbnail": thumbnail_path,
            "status": "exists",
        }

    # Download the song
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

    if not os.path.exists(mp3_path):
        return None

    if not os.path.exists(thumbnail_path):
        url = f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"
        r = requests.get(url, timeout=10)
        if r.ok:
            with open(thumbnail_path, "wb") as f:
                f.write(r.content)

    try:
        song = Song(
            youtube_id=youtube_id,
            filename=title,
        )

        history = DownloadHistory(
            user_id=current_user.id,
            youtube_id=youtube_id,
            youtube_playlist_id=playlist_id,
            playlist_title=playlist_title,
        )

        db.add(song)
        db.add(history)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "youtube_id": youtube_id,
        "title": title,
        "thumbnail": thumbnail_path,
        "status": "downloaded",
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
        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Unable to download this YouTube video."
            )   

        return {
            "success": True,
            "type": "video",
            **result,
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the request: {str(e)}"
        )