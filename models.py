# models.py
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


# class News(SQLModel, table=True):
#     __tablename__ = "all_news"

#     id: Optional[int] = Field(default=None, primary_key=True)
#     title: str = Field(max_length=255, nullable=False)
#     description: Optional[str] = Field(default=None)
#     published_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
#     updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
#     deleted_at: Optional[datetime] = Field(default=None, nullable=True)


class News(SQLModel, table=True):
    __tablename__ = "news"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    published_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # deleted_at: Optional[datetime] = Field(default=None, nullable=True)

