from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Group


class GroupRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_slug(self, slug: str) -> Group | None:
        stmt = select(Group).where(Group.slug == slug)
        return await self.session.scalar(stmt)

    async def get_all(self) -> list[Group]:
        stmt = select(Group).order_by(Group.title)
        result = await self.session.scalars(stmt)
        return result.all()

    async def create(self, title: str, slug: str, description: str) -> Group:
        group = Group(title=title, slug=slug, description=description)
        self.session.add(group)
        await self.session.commit()
        await self.session.refresh(group)
        return group