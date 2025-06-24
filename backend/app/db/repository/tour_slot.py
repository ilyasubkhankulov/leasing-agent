from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import TourSlot
from .base import BaseRepository


class TourSlotRepository(BaseRepository[TourSlot]):
    def __init__(self):
        super().__init__(TourSlot)

    async def get_by_community_id(self, db: AsyncSession, community_id: str) -> List[TourSlot]:
        return await self.get_many_by_field(db, "community_id", community_id)

    async def get_available_slots(self, db: AsyncSession, community_id: str, start_date: datetime, end_date: datetime) -> List[TourSlot]:
        result = await db.execute(
            select(TourSlot).where(
                TourSlot.community_id == community_id,
                TourSlot.is_available == True,
                TourSlot.start_time >= start_date,
                TourSlot.end_time <= end_date,
                TourSlot.current_bookings < TourSlot.max_capacity
            ).order_by(TourSlot.start_time)
        )
        return result.scalars().all()

    async def book_slot(self, db: AsyncSession, slot_id: str) -> Optional[TourSlot]:
        slot = await self.get_by_id(db, slot_id)
        if not slot or slot.current_bookings >= slot.max_capacity:
            return None
        
        slot.current_bookings += 1
        if slot.current_bookings >= slot.max_capacity:
            slot.is_available = False
        
        await db.commit()
        await db.refresh(slot)
        return slot

    async def cancel_booking(self, db: AsyncSession, slot_id: str) -> Optional[TourSlot]:
        slot = await self.get_by_id(db, slot_id)
        if not slot or slot.current_bookings <= 0:
            return None
        
        slot.current_bookings -= 1
        slot.is_available = True
        
        await db.commit()
        await db.refresh(slot)
        return slot