from datetime import datetime

from app.models.user import User
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.auth.database import Base


class PlayHistory(Base):
    __tablename__ = "play_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id",ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    user: Mapped["User"] = relationship(
        back_populates="play_history"
    )
    

    youtube_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("songs.youtube_id",ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user = relationship("User")
    song = relationship("Song")