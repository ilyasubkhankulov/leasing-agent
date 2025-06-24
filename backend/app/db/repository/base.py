from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: str) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, id: str, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return None
        
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: str) -> bool:
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return False
        
        await db.delete(db_obj)
        await db.commit()
        return True

    async def get_by_field(self, db: AsyncSession, field: str, value: Any) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(getattr(self.model, field) == value))
        return result.scalar_one_or_none()

    async def get_many_by_field(self, db: AsyncSession, field: str, value: Any) -> List[ModelType]:
        result = await db.execute(select(self.model).where(getattr(self.model, field) == value))
        return result.scalars().all()