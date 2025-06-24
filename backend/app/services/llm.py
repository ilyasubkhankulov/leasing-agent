import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from services.tools import check_availability, check_pet_policy, get_pricing
from pydantic import BaseModel
from config import settings
from core.logging import get_logger

logger = get_logger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class ActionResponse(BaseModel):
    action_type: str
    response_text: str
    tour_time: Optional[str] = None
    tour_date: Optional[str] = None
    unit_id: Optional[str] = None
    confirmation_required: Optional[bool] = None
    clarification_needed: Optional[str] = None
    follow_up: Optional[bool] = None
    tools_called: Optional[dict] = None
    tokens_used: Optional[int] = None

def serialize_for_json(obj: Any) -> Any:
    """Convert datetime objects to ISO format strings for JSON serialization"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    return obj

def _extract_inquiry_data(inquiry_data: Dict[str, Any]) -> Tuple[Dict[str, Any], str, Dict[str, Any], str, List[Dict[str, Any]]]:
    lead = inquiry_data["lead"]
    message = inquiry_data["message"]
    preferences = inquiry_data.get("preferences", {})
    community_id = inquiry_data["community_id"]
    conversation_history = inquiry_data.get("conversation_history", [])
    
    logger.info(f"Processing lead inquiry - Lead: {lead['email']}, Community: {community_id}, Bedrooms: {preferences.get('bedrooms')}, History: {len(conversation_history)} messages")
    
    return lead, message, preferences, community_id, conversation_history

def _build_tool_schemas() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": "Check available units in a community by bedroom count",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "community_id": {
                            "type": "string",
                            "description": "The community ID to search in"
                        },
                        "bedrooms": {
                            "type": "integer",
                            "description": "Number of bedrooms requested"
                        }
                    },
                    "required": ["community_id", "bedrooms"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_pet_policy",
                "description": "Check pet policy for a specific pet type in a community",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "community_id": {
                            "type": "string",
                            "description": "The community ID to check policy for"
                        },
                        "pet_type": {
                            "type": "string",
                            "description": "Type of pet (e.g., 'cat', 'dog')"
                        }
                    },
                    "required": ["community_id", "pet_type"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_pricing",
                "description": "Get pricing information for a specific unit",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "community_id": {
                            "type": "string",
                            "description": "The community ID"
                        },
                        "unit_id": {
                            "type": "string",
                            "description": "The unit ID to get pricing for"
                        },
                        "move_in_date": {
                            "type": "string",
                            "description": "Move-in date in YYYY-MM-DD format"
                        }
                    },
                    "required": ["community_id", "unit_id", "move_in_date"]
                }
            }
        }
    ]

def _build_preferences_info(preferences: Dict[str, Any]) -> str:
    preferences_info = ""
    if preferences:
        bedrooms = preferences.get("bedrooms")
        move_in = preferences.get("move_in")
        
        if bedrooms:
            preferences_info += f"- Looking for: {bedrooms} bedroom unit\n"
        if move_in:
            preferences_info += f"- Preferred move-in date: {move_in}\n"
    
    return preferences_info

def _build_system_prompt(lead: Dict[str, Any], community_id: str, preferences: Dict[str, Any]) -> str:
    preferences_info = _build_preferences_info(preferences)
    
    return f"""You are a helpful leasing agent assistant for the {community_id} community. 

Lead information:
- Name: {lead['name']}
- Email: {lead['email']}

Lead preferences:
{preferences_info}

Use the available tools to help answer their question. Reference the conversation history to provide contextual responses and avoid repeating information already discussed.

After gathering information and crafting your response, determine the appropriate next action:

1. "propose_tour": Use when you have enough information to suggest a specific tour time and have available units to show
2. "ask_clarification": Use when the lead's question is ambiguous or lacks key details beyond what's already provided
3. "handoff_human": Use when you cannot fulfill the request automatically (no available units, complex lease terms, etc.)
4. "tour_confirmed": Use when the lead confirms/accepts a previously proposed tour time with responses like "that works", "sounds good", "yes", "perfect", etc. This should end the conversation with a pleasant confirmation message.

Be friendly and helpful in your response. Reference their specific preferences and previous conversation when relevant."""

def _build_messages(system_prompt: str, conversation_history: List[Dict[str, Any]], message: str) -> List[Dict[str, Any]]:
    messages = [{"role": "system", "content": system_prompt}]
    
    if conversation_history:
        for hist_msg in conversation_history:
            messages.append({
                "role": hist_msg["role"],
                "content": hist_msg["content"]
            })
        logger.info(f"Added {len(conversation_history)} historical messages to context")
    
    messages.append({"role": "user", "content": message})
    return messages

async def _execute_single_tool(db: AsyncSession, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Executing tool: {function_name} with args: {arguments}")
    tool_start_time = time.time()
    
    try:
        if function_name == "check_availability":
            result = await check_availability(
                db, 
                arguments["community_id"], 
                arguments["bedrooms"]
            )
            logger.info(f"Availability check completed - Found {len(result.get('units', []))} units")
        elif function_name == "check_pet_policy":
            result = await check_pet_policy(
                db,
                arguments["community_id"],
                arguments["pet_type"]
            )
            logger.info(f"Pet policy check completed - Allowed: {result.get('allowed', False)}")
        elif function_name == "get_pricing":
            move_in_date = datetime.fromisoformat(arguments["move_in_date"])
            result = await get_pricing(
                db,
                arguments["community_id"],
                arguments["unit_id"],
                move_in_date
            )
            logger.info(f"Pricing check completed - Unit: {arguments['unit_id']}")
        else:
            result = {"error": f"Unknown function: {function_name}"}
            logger.error(f"Unknown function called: {function_name}")
            
    except Exception as e:
        result = {"error": f"Tool execution failed: {str(e)}"}
        logger.error(f"Tool {function_name} failed with error: {str(e)}")
    
    tool_time = time.time() - tool_start_time
    logger.info(f"Tool {function_name} executed in {tool_time:.2f}s")
    
    return result

async def _execute_tool_calls(db: AsyncSession, tool_calls: List[Any], messages: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    logger.info(f"Tool calls requested: {len(tool_calls)} functions")
    tools_called = {}
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        result = await _execute_single_tool(db, function_name, arguments)
        tools_called[function_name] = arguments
        
        serialized_result = serialize_for_json(result)
        
        messages.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": json.dumps(serialized_result)
        })
    
    return messages, tools_called

def _get_response_schema() -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "leasing_response",
            "schema": {
                "type": "object",
                "properties": {
                    "response_text": {
                        "type": "string",
                        "description": "The friendly response message to the lead"
                    },
                    "action_type": {
                        "type": "string",
                        "enum": ["propose_tour", "ask_clarification", "handoff_human", "tour_confirmed"],
                        "description": "The next action to take based on the inquiry"
                    },
                    "tour_time": {
                        "type": "string",
                        "description": "Proposed tour time (only for propose_tour action)"
                    },
                    "tour_date": {
                        "type": "string", 
                        "description": "Proposed tour date (only for propose_tour action)"
                    },
                    "unit_id": {
                        "type": "string",
                        "description": "Specific unit to tour (only for propose_tour action)"
                    },
                    "confirmation_required": {
                        "type": "boolean",
                        "description": "Whether tour confirmation is needed (only for propose_tour action)"
                    },
                    "clarification_needed": {
                        "type": "string",
                        "description": "What clarification is needed (only for ask_clarification action)"
                    }
                },
                "required": ["response_text", "action_type"],
                "additionalProperties": False
            }
        }
    }

def _get_structured_response(messages: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], int]:
    logger.info("Sending final request to OpenAI with tool results")
    
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        response_format=_get_response_schema()
    )
    
    tokens_used = response.usage.total_tokens if response.usage else 0
    logger.info(f"Final OpenAI call used {tokens_used} tokens")
    
    return json.loads(response.choices[0].message.content), tokens_used

def _handle_direct_response(messages: List[Dict[str, Any]], initial_content: str) -> Tuple[Dict[str, Any], int]:
    logger.info("No tool calls needed, processing direct response")
    
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages + [{"role": "assistant", "content": initial_content}],
        response_format=_get_response_schema()
    )
    
    tokens_used = response.usage.total_tokens if response.usage else 0
    logger.info(f"Structured response call used {tokens_used} tokens")
    
    return json.loads(response.choices[0].message.content), tokens_used

async def handle_lead_inquiry(db: AsyncSession, inquiry_data: Dict[str, Any]) -> ActionResponse:
    start_time = time.time()
    
    lead, message, preferences, community_id, conversation_history = _extract_inquiry_data(inquiry_data)
    tools = _build_tool_schemas()
    system_prompt = _build_system_prompt(lead, community_id, preferences)
    messages = _build_messages(system_prompt, conversation_history, message)
    
    logger.info(f"Sending request to OpenAI - Model: {settings.OPENAI_MODEL}, Total messages: {len(messages)}")
    
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    initial_response_time = time.time() - start_time
    logger.info(f"OpenAI initial response received - Time: {initial_response_time:.2f}s")
    
    total_tokens = response.usage.total_tokens if response.usage else 0
    logger.info(f"Initial OpenAI call used {total_tokens} tokens")
    
    message_response = response.choices[0].message
    
    if message_response.tool_calls:
        messages.append(message_response)
        messages, tools_called = await _execute_tool_calls(db, message_response.tool_calls, messages)
        
        structured_response, additional_tokens = _get_structured_response(messages)
        total_tokens += additional_tokens
        
        structured_response["tools_called"] = tools_called if tools_called else None
        structured_response["tokens_used"] = total_tokens
        
        total_time = time.time() - start_time
        logger.info(f"LLM processing completed - Action: {structured_response['action_type']}, Total time: {total_time:.2f}s, Total tokens: {total_tokens}, Lead: {lead['email']}")
        
        return ActionResponse(**structured_response)
    
    response_data, additional_tokens = _handle_direct_response(messages, message_response.content)
    total_tokens += additional_tokens
    
    response_data["tokens_used"] = total_tokens
    total_time = time.time() - start_time
    
    logger.info(f"Direct LLM processing completed - Action: {response_data['action_type']}, Total time: {total_time:.2f}s, Total tokens: {total_tokens}, Lead: {lead['email']}")
    return ActionResponse(**response_data)