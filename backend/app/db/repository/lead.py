from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import Lead, Conversation
from .base import BaseRepository


class LeadRepository(BaseRepository[Lead]):
    def __init__(self):
        super().__init__(Lead)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Lead]:
        return await self.get_by_field(db, "email", email)

    async def get_with_conversations(self, db: AsyncSession, lead_id: str) -> Optional[Lead]:
        result = await db.execute(
            select(Lead)
            .where(Lead.id == lead_id)
            .options(selectinload(Lead.conversations))
        )
        return result.scalar_one_or_none()

    async def search_by_name(self, db: AsyncSession, name_query: str) -> List[Lead]:
        result = await db.execute(
            select(Lead).where(Lead.name.ilike(f"%{name_query}%"))
        )
        return result.scalars().all()

    async def get_by_preferences(self, db: AsyncSession, bedrooms: Optional[int] = None, move_in_after: Optional[datetime] = None) -> List[Lead]:
        query = select(Lead)
        
        if bedrooms is not None:
            query = query.where(Lead.preferred_bedrooms == bedrooms)
        
        if move_in_after is not None:
            query = query.where(Lead.preferred_move_in >= move_in_after)
        
        result = await db.execute(query)
        return result.scalars().all()