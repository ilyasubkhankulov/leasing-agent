from datetime import datetime
from typing import List, Optional, Dict, Any
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

    async def create_or_get_by_email(self, db: AsyncSession, lead_data: Dict[str, Any]) -> Lead:
        existing_lead = await self.get_by_email(db, lead_data["email"])
        if existing_lead:
            update_data = {k: v for k, v in lead_data.items() if k != "email"}
            if update_data:
                for field, value in update_data.items():
                    if hasattr(existing_lead, field):
                        setattr(existing_lead, field, value)
                db.add(existing_lead)
                await db.flush()
            return existing_lead
        else:
            lead = Lead(**lead_data)
            db.add(lead)
            await db.flush()
            return lead

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