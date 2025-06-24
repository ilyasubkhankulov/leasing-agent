from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import PetPolicy, PetType
from .base import BaseRepository


class PetPolicyRepository(BaseRepository[PetPolicy]):
    def __init__(self):
        super().__init__(PetPolicy)

    async def get_by_community_id(self, db: AsyncSession, community_id: str) -> List[PetPolicy]:
        return await self.get_many_by_field(db, "community_id", community_id)

    async def get_by_pet_type(self, db: AsyncSession, community_id: str, pet_type: PetType) -> Optional[PetPolicy]:
        result = await db.execute(
            select(PetPolicy).where(
                PetPolicy.community_id == community_id,
                PetPolicy.pet_type == pet_type
            )
        )
        return result.scalar_one_or_none()

    async def get_allowed_pets(self, db: AsyncSession, community_id: str) -> List[PetPolicy]:
        result = await db.execute(
            select(PetPolicy).where(
                PetPolicy.community_id == community_id,
                PetPolicy.allowed == True
            )
        )
        return result.scalars().all()