from fastapi_pagination import Params

from app.exceptions import CannotFollowSelfError, UserNotFoundError
from app.models import User
from app.repositories.user import UserRepository
from app.schemas import ProfileResponse
from app.services.serializers import serialize_post_page


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    @property
    def session(self):
        return self.user_repo.session

    async def get_profile(
        self,
        target_username: str,
        current_user: User | None,
        params: Params | None = None,
    ) -> ProfileResponse:
        author = await self.user_repo.get_by_username(target_username)
        if not author:
            raise UserNotFoundError("Пользователь не найден")

        viewer_id = current_user.id if current_user else None
        posts_page = await self.user_repo.get_posts_by_author(
            author.id, params=params, viewer_id=viewer_id
        )
        posts_page = await serialize_post_page(self.session, posts_page, viewer_id=viewer_id)

        total_posts = await self.user_repo.count_posts_by_author(author.id)
        followers_count = await self.user_repo.count_followers(author.id)
        following_count = await self.user_repo.count_following(author.id)

        is_following = False
        if current_user and current_user.id != author.id:
            is_following = await self.user_repo.is_following(current_user.id, author.id)

        return {
            "author": author,
            "posts": posts_page,
            "is_following": is_following,
            "total_posts": total_posts,
            "followers_count": followers_count,
            "following_count": following_count,
        }

    async def follow_user(self, current_user: User, target_username: str) -> dict:
        author = await self.user_repo.get_by_username(target_username)
        if not author:
            raise UserNotFoundError("Пользователь не найден")
        if author.id == current_user.id:
            raise CannotFollowSelfError("Нельзя подписаться на себя")

        if not await self.user_repo.is_following(current_user.id, author.id):
            await self.user_repo.add_follow(current_user.id, author.id)

        return {"status": "following"}

    async def unfollow_user(self, current_user: User, target_username: str) -> dict:
        author = await self.user_repo.get_by_username(target_username)
        if not author:
            raise UserNotFoundError("Пользователь не найден")

        await self.user_repo.remove_follow(current_user.id, author.id)
        return {"status": "unfollowed"}
