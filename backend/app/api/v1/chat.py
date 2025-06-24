from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator, List
from datetime import datetime
import json
import asyncio
import time
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db_session, get_db_context
from db.repository import CommunityRepository, LeadRepository, ConversationRepository, MessageRepository
from services.llm import handle_lead_inquiry
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class Lead(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None


class Preferences(BaseModel):
    bedrooms: int
    move_in: str


class StartChatRequest(BaseModel):
    lead: Lead
    preferences: Preferences
    community_id: str


class StartChatResponse(BaseModel):
    lead_id: str
    conversation_id: str
    message: str


class ReplyRequest(BaseModel):
    lead_id: str
    conversation_id: str
    message: str


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
    logger.info("Fetching all communities")
    
    try:
        community_repo = CommunityRepository()
        communities = await community_repo.get_all(db)
        
        logger.info(f"Retrieved {len(communities)} communities")
        
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
    except Exception as e:
        logger.error(f"Failed to fetch communities: {e}")
        raise


@router.post("/start", response_model=StartChatResponse)
async def start_chat(request: StartChatRequest, db: AsyncSession = Depends(get_db_session)):
    logger.info(f"Starting chat - Lead: {request.lead.email}, Community: {request.community_id}, Bedrooms: {request.preferences.bedrooms}")
    
    try:
        lead_repo = LeadRepository()
        conversation_repo = ConversationRepository()
        
        move_in_date = datetime.fromisoformat(request.preferences.move_in)
        
        lead_data = {
            "name": request.lead.name,
            "email": request.lead.email,
            "phone": request.lead.phone,
            "preferred_bedrooms": request.preferences.bedrooms,
            "preferred_move_in": move_in_date
        }
        
        lead = await lead_repo.create_or_get_by_email(db, lead_data)
        logger.info(f"Lead processed - ID: {lead.id}, Email: {lead.email}")
        
        conversation_data = {
            "lead_id": lead.id,
            "community_id": request.community_id
        }
        conversation = await conversation_repo.create(db, conversation_data)
        logger.info(f"Conversation created - ID: {conversation.id}, Lead: {lead.id}, Community: {request.community_id}")
        
        response = StartChatResponse(
            lead_id=lead.id,
            conversation_id=conversation.id,
            message=f"Hi {lead.name}! I'm here to help you find the perfect {request.preferences.bedrooms}-bedroom apartment. What questions do you have?"
        )
        
        logger.info(f"Chat started successfully - Conversation: {conversation.id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to start chat for {request.lead.email}: {e}")
        await db.rollback()
        raise


async def generate_leasing_response(request: ReplyRequest) -> AsyncGenerator[str, None]:
    start_time = time.time()
    request_id = str(uuid.uuid4())
    logger.info(f"Processing reply - Lead: {request.lead_id}, Conversation: {request.conversation_id}, RequestID: {request_id}, Message: '{request.message[:100]}...'")
    
    try:
        async with get_db_context() as db:
            lead_repo = LeadRepository()
            message_repo = MessageRepository()
            lead = await lead_repo.get_by_id(db, request.lead_id)
            
            if not lead:
                logger.error(f"Lead not found: {request.lead_id}")
                raise ValueError("Lead not found")
            
            conversation_repo = ConversationRepository()
            conversation = await conversation_repo.get_by_id(db, request.conversation_id)
            
            if not conversation:
                logger.error(f"Conversation not found: {request.conversation_id}")
                raise ValueError("Conversation not found")
            
            # Get conversation history
            conversation_messages = await message_repo.get_by_conversation_id(db, request.conversation_id)
            logger.info(f"Retrieved {len(conversation_messages)} previous messages for conversation {request.conversation_id}")
            
            # Create the user message record
            user_message_data = {
                "conversation_id": request.conversation_id,
                "message_text": request.message,
                "request_id": request_id
            }
            user_message = await message_repo.create(db, user_message_data)
            logger.info(f"User message saved - ID: {user_message.id}")
            
            inquiry_data = {
                "lead": {
                    "name": lead.name,
                    "email": lead.email
                },
                "message": request.message,
                "conversation_history": [
                    {
                        "role": "user" if i % 2 == 0 else "assistant",
                        "content": msg.message_text if i % 2 == 0 else msg.reply_text,
                        "timestamp": msg.created_at.isoformat()
                    }
                    for i, msg in enumerate(conversation_messages)
                    if (i % 2 == 0 and msg.message_text) or (i % 2 == 1 and msg.reply_text)
                ],
                "preferences": {
                    "bedrooms": lead.preferred_bedrooms,
                    "move_in": lead.preferred_move_in.isoformat() if lead.preferred_move_in else None
                },
                "community_id": conversation.community_id
            }
            
            logger.info(f"Sending inquiry to LLM - Lead: {lead.email}, Community: {conversation.community_id}, History length: {len(inquiry_data['conversation_history'])}")
            action_response = await handle_lead_inquiry(db, inquiry_data)
            
            processing_time = time.time() - start_time
            logger.info(f"LLM response received - Action: {action_response.action_type}, Processing time: {processing_time:.2f}s")
            
            # Update user message with the reply and action info
            update_data = {
                "reply_text": action_response.response_text,
                "action": action_response.action_type,
                "llm_latency_ms": int(processing_time * 1000)
            }
            
            if action_response.action_type == "propose_tour" and action_response.tour_date and action_response.tour_time:
                try:
                    proposed_datetime = datetime.fromisoformat(f"{action_response.tour_date}T{action_response.tour_time}")
                    update_data["proposed_time"] = proposed_datetime
                except ValueError:
                    logger.warning(f"Failed to parse tour datetime: {action_response.tour_date}T{action_response.tour_time}")
            
            if hasattr(action_response, 'tools_called') and action_response.tools_called:
                update_data["tools_called"] = action_response.tools_called
            
            await message_repo.update(db, user_message.id, update_data)
            logger.info(f"Message updated with LLM response - ID: {user_message.id}")
            
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
                logger.info(f"Tour proposed - Unit: {action_response.unit_id}, Date: {action_response.tour_date}, Time: {action_response.tour_time}")
            elif action_response.action_type == "ask_clarification":
                action_data.update({
                    "clarification_needed": action_response.clarification_needed
                })
                logger.info(f"Clarification requested: {action_response.clarification_needed}")
            elif action_response.action_type == "handoff_human":
                action_data.update({
                    "follow_up": True
                })
                logger.info("Human handoff initiated")
            
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
            
            total_time = time.time() - start_time
            logger.info(f"Response streaming completed - Total time: {total_time:.2f}s, Lead: {lead.email}")
        
    except Exception as e:
        logger.error(f"Error generating response for conversation {request.conversation_id}: {e}")
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