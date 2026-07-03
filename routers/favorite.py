from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from app.auth.dependencies import get_current_user
from app.models import User

from app.models import Song ,Favorite
from app.auth.database import get_db
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/favorite",
    tags=["favorite"],
)


@router.post("/{youtube_id}")
def add_favorite(
    youtube_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    song = (
        db.query(Song)
        .filter(Song.youtube_id == youtube_id)
        .first()
    )

    if song is None:
        raise HTTPException(
            status_code=404,
            detail="Song not found",
        )

    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.id,
            Favorite.song_id == youtube_id,
        )
        .first()
    )

    if favorite:
        return {
            "message": "Already in favorites"
        }

    favorite = Favorite(
        user_id=current_user.id,
        song_id=youtube_id,
    )

    db.add(favorite)
    db.commit()

    return {
        "message": "Added to favorites"
    }

@router.get("/")
def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    songs = (
        db.query(Song)
        .join(
            Favorite,
            Song.youtube_id == Favorite.song_id,
        )
        .filter(
            Favorite.user_id == current_user.id
        )
        .all()
    )

    return songs

@router.delete("/{youtube_id}")
def remove_favorite(
    youtube_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.id,
            Favorite.song_id == youtube_id,
        )
        .first()
    )

    if favorite is None:
        raise HTTPException(
            status_code=404,
            detail="Favorite not found",
        )

    db.delete(favorite)
    db.commit()

    return {
        "message": "Removed from favorites"
    }