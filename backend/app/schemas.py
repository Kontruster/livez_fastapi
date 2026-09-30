from datetime import datetime
from typing import Optional

from fastapi_pagination import Page
from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, Field
import re
# class UserShort(BaseModel):
#     id: int
#     username: str
#     model_config = ConfigDict(from_attributes=True)

class UserRead(schemas.BaseUser[int]):
    username: str
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(schemas.BaseUserCreate):
    username: str
    email: EmailStr

class GroupRead(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    model_config = ConfigDict(from_attributes=True)

class GroupCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=2, max_length=64)
    description: str = ""

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", v):
            raise ValueError(
                "slug может содержать только a-z, 0-9 и дефис, "
                "и должен начинаться с буквы или цифры"
            )
        return v

class PostCreate(BaseModel):
    text: str
    group_id: Optional[int] = None
    image: Optional[str] = None

# class PostRead(PostCreate):
#     id: int
#     pub_date: datetime
#     author_id: int
#     model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    text: str

class CommentRead(CommentCreate):
    id: int
    pub_date: datetime
    # author_id: int
    author: UserRead
    model_config = ConfigDict(from_attributes=True)

class UserShort(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)

class PostList(BaseModel):
    id: int
    title: Optional[str] = None
    text: str
    pub_date: datetime
    image: Optional[str] = None
    author: UserRead
    author_id: int
    group_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class PostDetail(BaseModel):
    id: int
    text: str
    pub_date: datetime
    image: Optional[str] = None
    author: UserRead
    group: Optional[GroupRead] = None
    comments: list[CommentRead] = []
    model_config = ConfigDict(from_attributes=True)

class PostDetailResponse(BaseModel):
    post: PostDetail
    author_post_count: int

class ProfileResponse(BaseModel):
    author: UserRead
    posts: Page[PostList]
    is_following: bool
    total_posts: int
    model_config = ConfigDict(from_attributes=True)

class GroupDetailResponse(BaseModel):
    group: GroupRead
    posts: Page[PostList]
