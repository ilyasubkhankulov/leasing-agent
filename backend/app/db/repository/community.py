from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import Community, Unit, PetPolicy, TourSlot
from .base import BaseRepository


class CommunityRepository(BaseRepository[Community]):
    def __init__(self):
        super().__init__(Community)

    async def get_with_units(self, db: AsyncSession, community_id: str) -> Optional[Community]:
        result = await db.execute(
            select(Community)
            .where(Community.id == community_id)
            .options(selectinload(Community.units))
        )
        return result.scalar_one_or_none()

    async def get_with_all_relations(self, db: AsyncSession, community_id: str) -> Optional[Community]:
        result = await db.execute(
            select(Community)
            .where(Community.id == community_id)
            .options(
                selectinload(Community.units),
                selectinload(Community.pet_policies),
                selectinload(Community.tour_slots)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Community]:
        return await self.get_by_field(db, "name", name)

    async def search_by_address(self, db: AsyncSession, address_query: str) -> List[Community]:
        result = await db.execute(
            select(Community).where(Community.address.ilike(f"%{address_query}%"))
        )
        return result.scalars().all()