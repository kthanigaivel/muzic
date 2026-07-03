from datetime import datetime

from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.auth.database import Base


class DownloadHistory(Base):
    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    youtube_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("songs.youtube_id"),
        nullable=False,
        index=True,
    )

    youtube_playlist_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    playlist_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user = relationship("User")
    song = relationship("Song")