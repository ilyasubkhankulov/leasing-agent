import json
import time
from typing import Dict, Any, List, Optional
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

async def handle_lead_inquiry(db: AsyncSession, inquiry_data: Dict[str, Any]) -> ActionResponse:
    start_time = time.time()
    lead = inquiry_data["lead"]
    message = inquiry_data["message"]
    preferences = inquiry_data.get("preferences", {})
    community_id = inquiry_data["community_id"]
    conversation_history = inquiry_data.get("conversation_history", [])
    
    logger.info(f"Processing lead inquiry - Lead: {lead['email']}, Community: {community_id}, Bedrooms: {preferences.get('bedrooms')}, History: {len(conversation_history)} messages")
    
    tools = [
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
    
    preferences_info = ""
    if preferences:
        bedrooms = preferences.get("bedrooms")
        move_in = preferences.get("move_in")
        
        if bedrooms:
            preferences_info += f"- Looking for: {bedrooms} bedroom unit\n"
        if move_in:
            preferences_info += f"- Preferred move-in date: {move_in}\n"
    
    system_prompt = f"""You are a helpful leasing agent assistant for the {community_id} community. 

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

Be friendly and helpful in your response. Reference their specific preferences and previous conversation when relevant."""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    if conversation_history:
        for hist_msg in conversation_history:
            messages.append({
                "role": hist_msg["role"],
                "content": hist_msg["content"]
            })
        logger.info(f"Added {len(conversation_history)} historical messages to context")
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    logger.info(f"Sending request to OpenAI - Model: {settings.OPENAI_MODEL}, Total messages: {len(messages)}")
    
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    initial_response_time = time.time() - start_time
    logger.info(f"OpenAI initial response received - Time: {initial_response_time:.2f}s")
    
    message_response = response.choices[0].message
    tools_called = {}
    
    if message_response.tool_calls:
        logger.info(f"Tool calls requested: {len(message_response.tool_calls)} functions")
        messages.append(message_response)
        
        for tool_call in message_response.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            logger.info(f"Executing tool: {function_name} with args: {arguments}")
            tool_start_time = time.time()
            
            if function_name == "check_availability":
                result = await check_availability(
                    db, 
                    arguments["community_id"], 
                    arguments["bedrooms"]
                )
                tools_called[function_name] = arguments
                logger.info(f"Availability check completed - Found {len(result.get('units', []))} units")
            elif function_name == "check_pet_policy":
                result = await check_pet_policy(
                    db,
                    arguments["community_id"],
                    arguments["pet_type"]
                )
                tools_called[function_name] = arguments
                logger.info(f"Pet policy check completed - Allowed: {result.get('allowed', False)}")
            elif function_name == "get_pricing":
                move_in_date = datetime.fromisoformat(arguments["move_in_date"])
                result = await get_pricing(
                    db,
                    arguments["community_id"],
                    arguments["unit_id"],
                    move_in_date
                )
                tools_called[function_name] = arguments
                logger.info(f"Pricing check completed - Unit: {arguments['unit_id']}")
            else:
                result = {"error": f"Unknown function: {function_name}"}
                logger.error(f"Unknown function called: {function_name}")
            
            tool_time = time.time() - tool_start_time
            logger.info(f"Tool {function_name} executed in {tool_time:.2f}s")
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(result)
            })
        
        logger.info("Sending final request to OpenAI with tool results")
        final_response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            response_format={
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
                                "enum": ["propose_tour", "ask_clarification", "handoff_human"],
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
        )
        
        structured_response = json.loads(final_response.choices[0].message.content)
        structured_response["tools_called"] = tools_called if tools_called else None
        total_time = time.time() - start_time
        
        logger.info(f"LLM processing completed - Action: {structured_response['action_type']}, Total time: {total_time:.2f}s, Lead: {lead['email']}")
        return ActionResponse(**structured_response)
    
    logger.info("No tool calls needed, processing direct response")
    structured_response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages + [{"role": "assistant", "content": message_response.content}],
        response_format={
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
                            "enum": ["propose_tour", "ask_clarification", "handoff_human"],
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
    )
    
    response_data = json.loads(structured_response.choices[0].message.content)
    total_time = time.time() - start_time
    
    logger.info(f"Direct LLM processing completed - Action: {response_data['action_type']}, Total time: {total_time:.2f}s, Lead: {lead['email']}")
    return ActionResponse(**response_data)