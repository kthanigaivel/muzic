from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Column,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from app.auth.database import Base

class Favorite(Base):
    __tablename__ = "favorites"
    
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "song_id",
            name="uq_user_song_favorite",
        ),
    )
        

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    song_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("songs.youtube_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user: Mapped["User"] = relationship(
        back_populates="favorites"
    )

    song: Mapped["Song"] = relationship(
        back_populates="favorites"
    )