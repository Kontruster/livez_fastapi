from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class GroupRead(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    text: str
    group_id: Optional[int] = None
    image: Optional[str] = None  # В FastAPI файлы обрабатываются отдельно

class PostRead(PostCreate):
    id: int
    pub_date: datetime
    author_id: int
    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    text: str

class CommentRead(CommentCreate):
    id: int
    pub_date: datetime
    author_id: int
    model_config = ConfigDict(from_attributes=True)