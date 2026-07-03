import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.database import get_db
from app.auth.dependencies import get_current_user
from app.models import User, Song

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