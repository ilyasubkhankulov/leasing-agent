from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import Boolean as SA_Boolean
from sqlalchemy import Column as SA_Column
from sqlalchemy import DateTime as SA_DateTime
from sqlalchemy import Enum as SA_Enum
from sqlalchemy import Float as SA_Float
from sqlalchemy import ForeignKey as SA_ForeignKey
from sqlalchemy import Integer as SA_Integer
from sqlalchemy import String as SA_String
from sqlalchemy import Text as SA_Text
from sqlalchemy.dialects.postgresql import JSONB as SA_JSONB
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel


class ActionType(str, PyEnum):
    PROPOSE_TOUR = "propose_tour"
    ASK_CLARIFICATION = "ask_clarification"
    HANDOFF_HUMAN = "handoff_human"
    TOUR_CONFIRMED = "tour_confirmed"


class PetType(str, PyEnum):
    CAT = "cat"
    DOG = "dog"
    BIRD = "bird"
    FISH = "fish"
    OTHER = "other"


class Community(SQLModel, table=True):
    __tablename__ = "communities"
    
    id: str = Field(
        primary_key=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"server_default": func.nanoid()},
    )
    name: str = Field(sa_column=SA_Column(SA_String(255), nullable=False))
    address: str = Field(sa_column=SA_Column(SA_String(500), nullable=False))
    phone: Optional[str] = Field(
        default=None, sa_column=SA_Column(SA_String(20), nullable=True)
    )
    email: Optional[str] = Field(
        default=None, sa_column=SA_Column(SA_String(255), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    
    units: List["Unit"] = Relationship(back_populates="community")
    pet_policies: List["PetPolicy"] = Relationship(back_populates="community")
    tour_slots: List["TourSlot"] = Relationship(back_populates="community")


class Unit(SQLModel, table=True):
    __tablename__ = "units"
    
    id: str = Field(
        primary_key=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"server_default": func.nanoid()},
    )
    community_id: str = Field(
        sa_column=SA_Column(
            SA_String(50), SA_ForeignKey("communities.id"), nullable=False, index=True
        )
    )
    unit_number: str = Field(sa_column=SA_Column(SA_String(20), nullable=False))
    bedrooms: int = Field(sa_column=SA_Column(SA_Integer, nullable=False, index=True))
    bathrooms: float = Field(sa_column=SA_Column(SA_Float, nullable=False))
    square_feet: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    description: Optional[str] = Field(
        default=None, sa_column=SA_Column(SA_Text, nullable=True)
    )
    base_rent: int = Field(sa_column=SA_Column(SA_Integer, nullable=False))
    is_available: bool = Field(
        default=True, sa_column=SA_Column(SA_Boolean, default=True, nullable=False)
    )
    available_date: Optional[datetime] = Field(
        default=None, sa_column=SA_Column(SA_DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    
    community: Optional[Community] = Relationship(back_populates="units")
    pricing: List["UnitPricing"] = Relationship(back_populates="unit")


class PetPolicy(SQLModel, table=True):
    __tablename__ = "pet_policies"
    
    id: str = Field(
        primary_key=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"server_default": func.nanoid()},
    )
    community_id: str = Field(
        sa_column=SA_Column(
            SA_String(50), SA_ForeignKey("communities.id"), nullable=False, index=True
        )
    )
    pet_type: PetType = Field(
        sa_column=SA_Column(
            SA_Enum(PetType, name="pet_type", create_type=False),
            nullable=False,
            index=True,
        )
    )
    allowed: bool = Field(
        default=True, sa_column=SA_Column(SA_Boolean, default=True, nullable=False)
    )
    fee: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    deposit: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    monthly_rent: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    max_count: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    weight_limit: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    notes: Optional[str] = Field(
        default=None, sa_column=SA_Column(SA_Text, nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    
    community: Optional[Community] = Relationship(back_populates="pet_policies")


class UnitPricing(SQLModel, table=True):
    __tablename__ = "unit_pricing"
    
    id: str = Field(
        primary_key=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"server_default": func.nanoid()},
    )
    unit_id: str = Field(
        sa_column=SA_Column(
            SA_String(50), SA_ForeignKey("units.id"), nullable=False, index=True
        )
    )
    move_in_date: datetime = Field(
        sa_column=SA_Column(SA_DateTime(timezone=True), nullable=False, index=True)
    )
    rent: int = Field(sa_column=SA_Column(SA_Integer, nullable=False))
    special_offer: Optional[str] = Field(
        default=None, sa_column=SA_Column(SA_String(255), nullable=True)
    )
    special_discount: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    effective_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    expires_date: Optional[datetime] = Field(
        default=None, sa_column=SA_Column(SA_DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    
    unit: Optional[Unit] = Relationship(back_populates="pricing")


class TourSlot(SQLModel, table=True):
    __tablename__ = "tour_slots"
    
    id: str = Field(
        primary_key=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"server_default": func.nanoid()},
    )
    community_id: str = Field(
        sa_column=SA_Column(
            SA_String(50), SA_ForeignKey("communities.id"), nullable=False, index=True
        )
    )
    start_time: datetime = Field(
        sa_column=SA_Column(SA_DateTime(timezone=True), nullable=False, index=True)
    )
    end_time: datetime = Field(
        sa_column=SA_Column(SA_DateTime(timezone=True), nullable=False)
    )
    is_available: bool = Field(
        default=True, sa_column=SA_Column(SA_Boolean, default=True, nullable=False)
    )
    max_capacity: int = Field(
        default=1, sa_column=SA_Column(SA_Integer, default=1, nullable=False)
    )
    current_bookings: int = Field(
        default=0, sa_column=SA_Column(SA_Integer, default=0, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    
    community: Optional[Community] = Relationship(back_populates="tour_slots")


class Lead(SQLModel, table=True):
    __tablename__ = "leads"
    
    id: str = Field(
        primary_key=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"server_default": func.nanoid()},
    )
    name: str = Field(sa_column=SA_Column(SA_String(255), nullable=False))
    email: str = Field(
        sa_column=SA_Column(SA_String(255), nullable=False, index=True)
    )
    phone: Optional[str] = Field(
        default=None, sa_column=SA_Column(SA_String(20), nullable=True)
    )
    preferred_bedrooms: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    preferred_move_in: Optional[datetime] = Field(
        default=None, sa_column=SA_Column(SA_DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    
    conversations: List["Conversation"] = Relationship(back_populates="lead")


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    
    id: str = Field(
        primary_key=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"server_default": func.nanoid()},
    )
    lead_id: str = Field(
        sa_column=SA_Column(
            SA_String(50), SA_ForeignKey("leads.id"), nullable=False, index=True
        )
    )
    community_id: str = Field(
        sa_column=SA_Column(
            SA_String(50), SA_ForeignKey("communities.id"), nullable=False, index=True
        )
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    
    lead: Optional[Lead] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    
    id: str = Field(
        primary_key=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"server_default": func.nanoid()},
    )
    conversation_id: str = Field(
        sa_column=SA_Column(
            SA_String(50), SA_ForeignKey("conversations.id"), nullable=False, index=True
        )
    )
    message_text: str = Field(sa_column=SA_Column(SA_Text, nullable=False))
    reply_text: Optional[str] = Field(
        default=None, sa_column=SA_Column(SA_Text, nullable=True)
    )
    action: Optional[ActionType] = Field(
        default=None,
        sa_column=SA_Column(
            SA_Enum(ActionType, name="action_type", create_type=False), nullable=True
        ),
    )
    proposed_time: Optional[datetime] = Field(
        default=None, sa_column=SA_Column(SA_DateTime(timezone=True), nullable=True)
    )
    tools_called: Optional[dict] = Field(
        default=None, sa_column=SA_Column(SA_JSONB, nullable=True)
    )
    llm_tokens_used: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    llm_latency_ms: Optional[int] = Field(
        default=None, sa_column=SA_Column(SA_Integer, nullable=True)
    )
    request_id: str = Field(
        sa_column=SA_Column(SA_String(50), nullable=False, index=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
    
class ToolCall(SQLModel, table=True):
    __tablename__ = "tool_calls"
    
    id: str = Field(
        primary_key=True,
        index=True,
        max_length=50,
        sa_column_kwargs={"server_default": func.nanoid()},
    )
    function_name: str = Field(sa_column=SA_Column(SA_String(100), nullable=False, index=True))
    arguments: dict = Field(sa_column=SA_Column(SA_JSONB, nullable=False))
    response: dict = Field(sa_column=SA_Column(SA_JSONB, nullable=False))
    execution_time_ms: int = Field(sa_column=SA_Column(SA_Integer, nullable=False))
    success: bool = Field(sa_column=SA_Column(SA_Boolean, nullable=False))
    error_message: Optional[str] = Field(
        default=None, sa_column=SA_Column(SA_Text, nullable=True)
    )
    conversation_id: Optional[str] = Field(
        default=None, 
        sa_column=SA_Column(
            SA_String(50), SA_ForeignKey("conversations.id"), nullable=True, index=True
        )
    )
    request_id: Optional[str] = Field(
        default=None, sa_column=SA_Column(SA_String(50), nullable=True, index=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=SA_Column(
            SA_DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    
    conversation: Optional[Conversation] = Relationship()