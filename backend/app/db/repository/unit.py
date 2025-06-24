from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import Unit, UnitPricing
from .base import BaseRepository


class UnitRepository(BaseRepository[Unit]):
    def __init__(self):
        super().__init__(Unit)

    async def get_by_community_id(self, db: AsyncSession, community_id: str) -> List[Unit]:
        return await self.get_many_by_field(db, "community_id", community_id)

    async def get_available_units(self, db: AsyncSession, community_id: str) -> List[Unit]:
        result = await db.execute(
            select(Unit).where(
                Unit.community_id == community_id,
                Unit.is_available == True
            )
        )
        return result.scalars().all()

    async def get_by_bedrooms(self, db: AsyncSession, bedrooms: int, community_id: Optional[str] = None) -> List[Unit]:
        query = select(Unit).where(Unit.bedrooms == bedrooms)
        if community_id:
            query = query.where(Unit.community_id == community_id)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_with_pricing(self, db: AsyncSession, unit_id: str) -> Optional[Unit]:
        result = await db.execute(
            select(Unit)
            .where(Unit.id == unit_id)
            .options(selectinload(Unit.pricing))
        )
        return result.scalar_one_or_none()

    async def get_by_unit_number(self, db: AsyncSession, community_id: str, unit_number: str) -> Optional[Unit]:
        result = await db.execute(
            select(Unit).where(
                Unit.community_id == community_id,
                Unit.unit_number == unit_number
            )
        )
        return result.scalar_one_or_none()