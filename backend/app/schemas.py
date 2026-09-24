from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional
from fastapi_pagination import Page
from fastapi_users import schemas


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
    author: UserRead  # Вложенный автор комментария
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

