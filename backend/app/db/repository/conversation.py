from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models import Conversation, Message
from .base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self):
        super().__init__(Conversation)

    async def get_by_lead_id(self, db: AsyncSession, lead_id: str) -> List[Conversation]:
        return await self.get_many_by_field(db, "lead_id", lead_id)

    async def get_by_community_id(self, db: AsyncSession, community_id: str) -> List[Conversation]:
        return await self.get_many_by_field(db, "community_id", community_id)

    async def get_with_messages(self, db: AsyncSession, conversation_id: str) -> Optional[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def get_latest_for_lead(self, db: AsyncSession, lead_id: str, community_id: str) -> Optional[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.lead_id == lead_id,
                Conversation.community_id == community_id
            )
            .order_by(Conversation.created_at.desc())
        )
        return result.scalar_one_or_none()