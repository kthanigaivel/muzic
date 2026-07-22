import os

from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session

from app.auth.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Song , Favorite,PlayHistory,DownloadHistory
from app.schemas.song import DeleteSongsRequest

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

DOWNLOAD_DIR = "/opt/muzic/downloads"


@router.post("/cleanup/downloads")
def cleanup_downloads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
 

    valid_ids = {
        song.youtube_id
        for song in db.query(Song.youtube_id).all()
    }

    removed = []
    kept = 0

    for filename in os.listdir(DOWNLOAD_DIR):

        path = os.path.join(DOWNLOAD_DIR, filename)

        if not os.path.isfile(path):
            continue

        youtube_id, _ = os.path.splitext(filename)

        if youtube_id in valid_ids:
            kept += 1
            continue

        try:
            os.remove(path)
            removed.append(filename)
        except Exception:
            pass

    return {
        "success": True,
        "kept": kept,
        "deleted": len(removed),
        "files": removed,
    }
    
    
@router.delete("/delete")
def remove_songs(
    payload: DeleteSongsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.username != "admin":
        raise HTTPException(
            status_code=403,
            detail="Permission denied. Only admin can delete songs.",
        )

    not_found = []

    try:
        for youtube_id in payload.youtube_ids:
            song = (
                db.query(Song)
                .filter(Song.youtube_id == youtube_id)
                .first()
            )

            if not song:
                not_found.append(youtube_id)
                continue

            db.query(PlayHistory).filter(
                PlayHistory.youtube_id == youtube_id
            ).delete(synchronize_session=False)

            db.query(Favorite).filter(
                Favorite.song_id == youtube_id
            ).delete(synchronize_session=False)

            db.query(DownloadHistory).filter(
                DownloadHistory.youtube_id == youtube_id
            ).delete(synchronize_session=False)

            db.delete(song)

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Songs deleted successfully",
        "not_found": not_found,
    }