from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator, List
from datetime import datetime
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db_session
from db.repository import CommunityRepository
from services.llm import handle_lead_inquiry

router = APIRouter(prefix="/chat", tags=["chat"])


class Lead(BaseModel):
    name: str
    email: str


class Preferences(BaseModel):
    bedrooms: int
    move_in: str


class ReplyRequest(BaseModel):
    lead: Lead
    message: str
    preferences: Preferences
    community_id: str


class ReplyResponse(BaseModel):
    reply: str
    action: str
    proposed_time: Optional[str] = None


class StreamEvent(BaseModel):
    type: str
    data: dict


class CommunityResponse(BaseModel):
    id: str
    name: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None


@router.get("/communities", response_model=List[CommunityResponse])
async def get_communities(db: AsyncSession = Depends(get_db_session)):
    community_repo = CommunityRepository()
    communities = await community_repo.get_all(db)
    
    return [
        CommunityResponse(
            id=community.id,
            name=community.name,
            address=community.address,
            phone=community.phone,
            email=community.email
        )
        for community in communities
    ]


async def generate_leasing_response(request: ReplyRequest, db: AsyncSession) -> AsyncGenerator[str, None]:
    try:
        inquiry_data = {
            "lead": {
                "name": request.lead.name,
                "email": request.lead.email
            },
            "message": request.message,
            "preferences": {
                "bedrooms": request.preferences.bedrooms,
                "move_in": request.preferences.move_in
            },
            "community_id": request.community_id
        }
        
        action_response = await handle_lead_inquiry(db, inquiry_data)
        
        words = action_response.response_text.split()
        current_chunk = ""
        
        for i, word in enumerate(words):
            current_chunk += word + " "
            
            if len(current_chunk.split()) >= 4 or i == len(words) - 1:
                event = StreamEvent(
                    type="content_delta",
                    data={"content": current_chunk}
                )
                yield f"data: {event.model_dump_json()}\n\n"
                current_chunk = ""
                await asyncio.sleep(0.1)
        
        action_data = {
            "action": action_response.action_type
        }
        
        if action_response.action_type == "propose_tour":
            action_data.update({
                "tour_time": action_response.tour_time,
                "tour_date": action_response.tour_date,
                "unit_id": action_response.unit_id,
                "confirmation_required": action_response.confirmation_required or True
            })
        elif action_response.action_type == "ask_clarification":
            action_data.update({
                "clarification_needed": action_response.clarification_needed
            })
        elif action_response.action_type == "handoff_human":
            action_data.update({
                "follow_up": True
            })
        
        event = StreamEvent(
            type="action_determined",
            data=action_data
        )
        yield f"data: {event.model_dump_json()}\n\n"
        
        event = StreamEvent(
            type="response_complete",
            data={"reply": action_response.response_text, **action_data}
        )
        yield f"data: {event.model_dump_json()}\n\n"
        
    except Exception as e:
        error_event = StreamEvent(
            type="error",
            data={"error": str(e)}
        )
        yield f"data: {error_event.model_dump_json()}\n\n"


@router.post("/reply")
async def reply_stream(request: ReplyRequest, db: AsyncSession = Depends(get_db_session)):
    return StreamingResponse(
        generate_leasing_response(request, db),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )