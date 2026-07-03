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


class Song(Base):
    __tablename__ = "songs"

    youtube_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    

    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="song",
        cascade="all, delete-orphan",
    )
    
