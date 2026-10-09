from app.exceptions import GroupAlreadyExistsError, GroupNotFoundError
from app.models import Group, User
from app.repositories.group import GroupRepository
from app.schemas import GroupCreate, GroupDetail, GroupRead


class GroupService:
    def __init__(self, group_repo: GroupRepository):
        self.group_repo = group_repo

    async def get_all_groups(self) -> list[GroupRead]:
        groups = await self.group_repo.get_all()
        return [GroupRead.model_validate(g) for g in groups]

    async def get_group(self, slug: str) -> GroupRead:
        group = await self.group_repo.get_by_slug(slug)
        if not group:
            raise GroupNotFoundError("Сообщество не найдено")
        return GroupRead.model_validate(group)

    async def create_group(self, form: GroupCreate, owner: User) -> Group:
        existing = await self.group_repo.get_by_slug(form.slug)
        if existing:
            raise GroupAlreadyExistsError(f"Группа со slug '{form.slug}' уже существует")

        group = await self.group_repo.create(
            title=form.title,
            slug=form.slug,
            description=form.description,
            is_private=form.is_private,
        )
        # Создатель сразу становится участником (иначе не сможет постить
        # в собственную приватную группу).
        await self.group_repo.add_member(group.id, owner.id)
        return group

    async def get_group_detail(self, slug: str, viewer: User | None = None) -> GroupDetail:
        group = await self.group_repo.get_by_slug(slug)
        if not group:
            raise GroupNotFoundError("Сообщество не найдено")

        detail = GroupDetail.model_validate(group)
        detail.members_count = await self.group_repo.count_members(group.id)
        detail.is_member = viewer is not None and await self.group_repo.is_member(
            group.id, viewer.id
        )
        return detail

    async def join_group(self, slug: str, user: User) -> GroupDetail:
        group = await self.group_repo.get_by_slug(slug)
        if not group:
            raise GroupNotFoundError("Сообщество не найдено")

        await self.group_repo.add_member(group.id, user.id)

        detail = GroupDetail.model_validate(group)
        detail.members_count = await self.group_repo.count_members(group.id)
        detail.is_member = True
        return detail

    async def leave_group(self, slug: str, user: User) -> GroupDetail:
        group = await self.group_repo.get_by_slug(slug)
        if not group:
            raise GroupNotFoundError("Сообщество не найдено")

        await self.group_repo.remove_member(group.id, user.id)

        detail = GroupDetail.model_validate(group)
        detail.members_count = await self.group_repo.count_members(group.id)
        detail.is_member = False
        return detail
