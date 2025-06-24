from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import ToolCall
from .base import BaseRepository


class ToolCallRepository(BaseRepository[ToolCall]):
    def __init__(self):
        super().__init__(ToolCall)

    async def get_by_conversation_id(self, db: AsyncSession, conversation_id: str) -> List[ToolCall]:
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.conversation_id == conversation_id)
            .order_by(ToolCall.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_function_name(self, db: AsyncSession, function_name: str) -> List[ToolCall]:
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.function_name == function_name)
            .order_by(ToolCall.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_request_id(self, db: AsyncSession, request_id: str) -> List[ToolCall]:
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.request_id == request_id)
            .order_by(ToolCall.created_at.asc())
        )
        return result.scalars().all()

    async def get_failed_calls(self, db: AsyncSession) -> List[ToolCall]:
        result = await db.execute(
            select(ToolCall)
            .where(ToolCall.success == False)
            .order_by(ToolCall.created_at.desc())
        )
        return result.scalars().all()