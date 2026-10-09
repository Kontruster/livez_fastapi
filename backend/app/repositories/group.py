from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Group, GroupMember


class GroupRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_slug(self, slug: str) -> Group | None:
        stmt = select(Group).where(Group.slug == slug)
        return await self.session.scalar(stmt)

    async def get_by_id(self, group_id: int) -> Group | None:
        return await self.session.get(Group, group_id)

    async def get_all(self) -> list[Group]:
        stmt = select(Group).order_by(Group.title)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def create(
        self, title: str, slug: str, description: str, is_private: bool = False
    ) -> Group:
        group = Group(title=title, slug=slug, description=description, is_private=is_private)
        self.session.add(group)
        await self.session.flush()
        return group

    # ---------- Членство ----------

    async def is_member(self, group_id: int, user_id: int) -> bool:
        stmt = select(GroupMember.id).where(
            GroupMember.group_id == group_id, GroupMember.user_id == user_id
        )
        return (await self.session.scalar(stmt)) is not None

    async def count_members(self, group_id: int) -> int:
        stmt = select(func.count(GroupMember.id)).where(GroupMember.group_id == group_id)
        return await self.session.scalar(stmt) or 0

    async def add_member(self, group_id: int, user_id: int) -> None:
        if not await self.is_member(group_id, user_id):
            self.session.add(GroupMember(group_id=group_id, user_id=user_id))
            await self.session.flush()

    async def remove_member(self, group_id: int, user_id: int) -> None:
        await self.session.execute(
            delete(GroupMember).where(
                GroupMember.group_id == group_id, GroupMember.user_id == user_id
            )
        )
        await self.session.flush()
