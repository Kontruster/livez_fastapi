from app.repositories.group import GroupRepository
from app.schemas import GroupCreate, GroupRead
from app.models import Group

class GroupAlreadyExistsError(Exception):
    pass

class GroupService:
    def __init__(self, group_repo: GroupRepository):
        self.group_repo = group_repo

    async def get_all_groups(self) -> list[GroupRead]:
        groups = await self.group_repo.get_all()
        return [GroupRead.model_validate(g) for g in groups]

    async def create_group(self, form: GroupCreate) -> Group:
        existing = await self.group_repo.get_by_slug(form.slug)
        if existing:
            raise GroupAlreadyExistsError(f"Группа со slug '{form.slug}' уже существует")
        return await self.group_repo.create(
            title=form.title,
            slug=form.slug,
            description=form.description,
        )