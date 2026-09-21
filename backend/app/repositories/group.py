from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Group
from fastapi_pagination.ext.sqlalchemy import paginate

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
