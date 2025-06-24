from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import UnitPricing
from .base import BaseRepository


class UnitPricingRepository(BaseRepository[UnitPricing]):
    def __init__(self):
        super().__init__(UnitPricing)

    async def get_by_unit_id(self, db: AsyncSession, unit_id: str) -> List[UnitPricing]:
        return await self.get_many_by_field(db, "unit_id", unit_id)

    async def get_current_pricing(self, db: AsyncSession, unit_id: str, move_in_date: datetime) -> Optional[UnitPricing]:
        result = await db.execute(
            select(UnitPricing).where(
                UnitPricing.unit_id == unit_id,
                UnitPricing.move_in_date <= move_in_date,
                UnitPricing.effective_date <= datetime.now(),
                (UnitPricing.expires_date.is_(None)) | (UnitPricing.expires_date > datetime.now())
            ).order_by(UnitPricing.move_in_date.desc())
        )
        return result.scalar_one_or_none()

    async def get_active_specials(self, db: AsyncSession, unit_id: str) -> List[UnitPricing]:
        current_time = datetime.now()
        result = await db.execute(
            select(UnitPricing).where(
                UnitPricing.unit_id == unit_id,
                UnitPricing.special_offer.is_not(None),
                UnitPricing.effective_date <= current_time,
                (UnitPricing.expires_date.is_(None)) | (UnitPricing.expires_date > current_time)
            )
        )
        return result.scalars().all()