from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Message, ActionType
from .base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self):
        super().__init__(Message)

    async def get_by_conversation_id(self, db: AsyncSession, conversation_id: str) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return result.scalars().all()

    async def get_by_request_id(self, db: AsyncSession, request_id: str) -> Optional[Message]:
        return await self.get_by_field(db, "request_id", request_id)

    async def get_by_action_type(self, db: AsyncSession, conversation_id: str, action_type: ActionType) -> List[Message]:
        result = await db.execute(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.action == action_type
            )
        )
        return result.scalars().all()

    async def get_recent_messages(self, db: AsyncSession, conversation_id: str, limit: int = 10) -> List[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_messages_with_tools(self, db: AsyncSession, conversation_id: str) -> List[Message]:
        result = await db.execute(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.tools_called.is_not(None)
            )
        )
        return result.scalars().all()