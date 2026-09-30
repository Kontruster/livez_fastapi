from app.repositories.group import GroupRepository
from app.schemas import GroupRead


class GroupService:
    def __init__(self, group_repo: GroupRepository):
        self.group_repo = group_repo

    async def get_all_groups(self) -> list[GroupRead]:
        groups = await self.group_repo.get_all()
        return [GroupRead.model_validate(g) for g in groups]
