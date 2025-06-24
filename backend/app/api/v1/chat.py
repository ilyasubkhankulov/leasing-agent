from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
from datetime import datetime
import json
import asyncio

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


async def generate_leasing_response(request: ReplyRequest) -> AsyncGenerator[str, None]:
    mock_response_parts = [
        f"Hi {request.lead.name}! ",
        "Thanks for your interest in our ",
        f"{request.preferences.bedrooms}-bedroom units. ",
        "I have great news - we have several available units that match your criteria! ",
        "Unit 12B is perfect and includes all modern amenities. ",
        "We welcome pets with just a one-time $50 fee. ",
        f"For your move-in date of {request.preferences.move_in}, ",
        "we can schedule a tour this Saturday between 10 AM and 2 PM. ",
        "Would 11 AM work for you?"
    ]
    
    try:
        full_response = ""
        
        for part in mock_response_parts:
            full_response += part
            
            event = StreamEvent(
                type="content_delta",
                data={"content": part}
            )
            yield f"data: {event.model_dump_json()}\n\n"
            
            await asyncio.sleep(0.1)
        
        action_data = {
            "action": "propose_tour",
            "tour_time": "11:00 AM",
            "tour_date": "2025-01-18",
            "unit_id": "12B",
            "confirmation_required": True
        }
        
        event = StreamEvent(
            type="action_determined",
            data=action_data
        )
        yield f"data: {event.model_dump_json()}\n\n"
        
        event = StreamEvent(
            type="response_complete",
            data={"reply": full_response, **action_data}
        )
        yield f"data: {event.model_dump_json()}\n\n"
        
    except Exception as e:
        error_event = StreamEvent(
            type="error",
            data={"error": str(e)}
        )
        yield f"data: {error_event.model_dump_json()}\n\n"


@router.post("/reply")
async def reply_stream(request: ReplyRequest):
    return StreamingResponse(
        generate_leasing_response(request),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )