import re
from datetime import datetime
from typing import Annotated

from fastapi_pagination import Page
from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, Field, field_validator

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

UsernameStr = Annotated[str, Field(min_length=3, max_length=50)]


def _validate_username(v: str) -> str:
    v = v.strip()
    if not USERNAME_RE.fullmatch(v):
        raise ValueError("Ник может содержать только латиницу, цифры, точку, дефис и подчёркивание")
    return v


# ---------- Пользователи ----------


class UserRead(schemas.BaseUser[int]):
    username: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserShort(BaseModel):
    id: int
    username: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.BaseUserCreate):
    username: UsernameStr

    _check_username = field_validator("username")(_validate_username)


class UsernameChange(BaseModel):
    username: UsernameStr

    _check_username = field_validator("username")(_validate_username)


class PasswordChange(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class AccountDelete(BaseModel):
    password: str = Field(min_length=1)


# ---------- Группы ----------


class GroupRead(BaseModel):
    id: int
    title: str
    slug: str
    description: str | None = ""
    is_private: bool = False

    model_config = ConfigDict(from_attributes=True)


class GroupCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=2, max_length=64)
    description: str = Field(default="", max_length=2000)
    is_private: bool = False

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not SLUG_RE.fullmatch(v):
            raise ValueError(
                "slug может содержать только a-z, 0-9 и дефис, "
                "и должен начинаться с буквы или цифры"
            )
        return v


class GroupDetail(GroupRead):
    """Группа с информацией о членстве текущего пользователя."""

    members_count: int = 0
    is_member: bool = False


# ---------- Картинки и посты ----------


class PostImageRead(BaseModel):
    id: int
    url: str
    position: int

    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    group_id: int | None = None
    image: str | None = None
    images: list[str] | None = Field(default=None, max_length=10)

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Текст поста не может быть пустым")
        return v

    @field_validator("images")
    @classmethod
    def check_images(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        if len(v) > 10:
            raise ValueError("Не больше 10 картинок на пост")
        return v


class PostUpdate(BaseModel):
    """PATCH: все поля опциональны, меняются только переданные."""

    text: str | None = Field(default=None, min_length=1, max_length=5000)
    group_id: int | None = None
    images: list[str] | None = Field(default=None, max_length=10)

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Текст поста не может быть пустым")
        return v


class PostList(BaseModel):
    id: int
    text: str
    pub_date: datetime
    image: str | None = None
    author: UserShort
    author_id: int
    group: GroupRead | None = None
    group_id: int | None = None
    images: list[PostImageRead] = []
    comments_count: int = 0
    likes_count: int = 0
    is_liked: bool = False

    model_config = ConfigDict(from_attributes=True)


class LikeState(BaseModel):
    """Результат лайка/дизлайка."""

    liked: bool
    likes_count: int


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    parent_id: int | None = None

    @field_validator("text")
    @classmethod
    def strip_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Комментарий не может быть пустым")
        return v


class CommentRead(BaseModel):
    id: int
    text: str
    pub_date: datetime
    author: UserShort
    post_id: int
    parent_id: int | None = None
    replies: list["CommentRead"] = []

    model_config = ConfigDict(from_attributes=True)


CommentRead.model_rebuild()


class PostDetail(BaseModel):
    id: int
    text: str
    pub_date: datetime
    image: str | None = None
    author: UserShort
    author_id: int
    group: GroupRead | None = None
    comments: list[CommentRead] = []
    images: list[PostImageRead] = []
    comments_count: int = 0
    likes_count: int = 0
    is_liked: bool = False

    model_config = ConfigDict(from_attributes=True)


class PostDetailResponse(BaseModel):
    post: PostDetail
    author_post_count: int


class ProfileResponse(BaseModel):
    author: UserRead
    posts: Page[PostList]
    is_following: bool
    total_posts: int
    followers_count: int = 0
    following_count: int = 0


class GroupDetailResponse(BaseModel):
    group: GroupDetail
    posts: Page[PostList]
