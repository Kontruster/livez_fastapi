from app.repositories.user import UserRepository
from app.schemas import ProfileResponse
from app.exceptions import UserNotFoundError, CannotFollowSelfError
from app.models import User

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_profile(self, target_username: str, current_user: User | None) -> ProfileResponse:
        author = await self.user_repo.get_by_username(target_username)
        if not author:
            raise UserNotFoundError("Пользователь не найден")

        posts_page = await self.user_repo.get_posts_by_author(author.id)
        total_posts = await self.user_repo.count_posts_by_author(author.id)

        is_following = False
        if current_user and current_user.id != author.id:
            is_following = await self.user_repo.is_following(current_user.id, author.id)

        # Возвращаем словарь, который Pydantic (ProfileResponse) сможет валидировать
        return {
            "author": author,
            "posts": posts_page,
            "is_following": is_following,
            "total_posts": total_posts
        }

    async def follow_user(self, current_user: User, target_username: str) -> dict:
        author = await self.user_repo.get_by_username(target_username)
        if not author:
            raise UserNotFoundError("Пользователь не найден")
        if author.id == current_user.id:
            raise CannotFollowSelfError("Нельзя подписаться на себя")

        is_following = await self.user_repo.is_following(current_user.id, author.id)
        if not is_following:
            await self.user_repo.add_follow(current_user.id, author.id)
            
        return {"status": "following"}

    async def unfollow_user(self, current_user: User, target_username: str) -> dict:
        author = await self.user_repo.get_by_username(target_username)
        if not author:
            raise UserNotFoundError("Пользователь не найден")

        await self.user_repo.remove_follow(current_user.id, author.id)
        return {"status": "unfollowed"}
