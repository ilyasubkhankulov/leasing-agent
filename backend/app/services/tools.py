from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from sqlalchemy.ext.asyncio import AsyncSession
from db.repository import UnitRepository, PetPolicyRepository, UnitPricingRepository, TourSlotRepository, ToolCallRepository
from core.logging import get_logger

logger = get_logger(__name__)

async def log_tool_call(
    db: AsyncSession,
    function_name: str,
    arguments: Dict[str, Any],
    response: Dict[str, Any],
    execution_time_ms: int,
    success: bool,
    error_message: Optional[str] = None,
    conversation_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> None:
    try:
        tool_call_repo = ToolCallRepository()
        tool_call_data = {
            "function_name": function_name,
            "arguments": arguments,
            "response": response,
            "execution_time_ms": execution_time_ms,
            "success": success,
            "error_message": error_message,
            "conversation_id": conversation_id,
            "request_id": request_id
        }
        await tool_call_repo.create(db, tool_call_data)
    except Exception as e:
        logger.error(f"Failed to log tool call for {function_name}: {e}")

async def check_availability(
    db: AsyncSession, 
    community_id: str, 
    bedrooms: int,
    conversation_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    function_name = "check_availability"
    arguments = {"community_id": community_id, "bedrooms": bedrooms}
    start_time = time.time()
    
    logger.info(f"Checking availability - Community: {community_id}, Bedrooms: {bedrooms}")
    
    try:
        unit_repo = UnitRepository()
        available_units = await unit_repo.get_available_units(db, community_id)
        logger.info(f"Retrieved {len(available_units)} total available units")
        
        filtered_units = [
            unit for unit in available_units 
            if unit.bedrooms == bedrooms
        ]
        logger.info(f"Filtered to {len(filtered_units)} units with {bedrooms} bedrooms")
        
        units_data = [
            {
                "id": unit.id,
                "unit_number": unit.unit_number,
                "bedrooms": unit.bedrooms,
                "bathrooms": unit.bathrooms,
                "square_feet": unit.square_feet,
                "is_available": unit.is_available
            }
            for unit in filtered_units
        ]
        
        result = {
            "units": units_data,
            "total_count": len(units_data),
            "community_id": community_id,
            "bedrooms_requested": bedrooms
        }
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Availability check completed - Returning {len(units_data)} matching units in {execution_time_ms}ms")
        
        await log_tool_call(
            db, function_name, arguments, result, execution_time_ms, True,
            conversation_id=conversation_id, request_id=request_id
        )
        
        return result
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_result = {
            "units": [],
            "total_count": 0,
            "community_id": community_id,
            "bedrooms_requested": bedrooms,
            "error": str(e)
        }
        
        logger.error(f"Error checking availability - Community: {community_id}, Bedrooms: {bedrooms}, Error: {e}")
        
        await log_tool_call(
            db, function_name, arguments, error_result, execution_time_ms, False,
            error_message=str(e), conversation_id=conversation_id, request_id=request_id
        )
        
        return error_result

async def check_pet_policy(
    db: AsyncSession, 
    community_id: str, 
    pet_type: str,
    conversation_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    function_name = "check_pet_policy"
    arguments = {"community_id": community_id, "pet_type": pet_type}
    start_time = time.time()
    
    logger.info(f"Checking pet policy - Community: {community_id}, Pet type: {pet_type}")
    
    try:
        pet_policy_repo = PetPolicyRepository()
        policy = await pet_policy_repo.get_by_pet_type(db, community_id, pet_type)
        
        if not policy:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result = None
            logger.info(f"No pet policy found - Community: {community_id}, Pet type: {pet_type}")
            
            await log_tool_call(
                db, function_name, arguments, {"policy_found": False}, execution_time_ms, True,
                conversation_id=conversation_id, request_id=request_id
            )
            
            return result
        
        result = {
            "pet_type": policy.pet_type,
            "allowed": policy.allowed,
            "deposit": policy.deposit,
            "monthly_fee": policy.monthly_rent,
            "weight_limit": policy.weight_limit,
            "max_count": policy.max_count
        }
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Pet policy found - Community: {community_id}, Pet type: {pet_type}, Allowed: {policy.allowed} in {execution_time_ms}ms")
        
        await log_tool_call(
            db, function_name, arguments, result, execution_time_ms, True,
            conversation_id=conversation_id, request_id=request_id
        )
        
        return result
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_result = {
            "pet_type": pet_type,
            "allowed": False,
            "error": str(e)
        }
        
        logger.error(f"Error checking pet policy - Community: {community_id}, Pet type: {pet_type}, Error: {e}")
        
        await log_tool_call(
            db, function_name, arguments, error_result, execution_time_ms, False,
            error_message=str(e), conversation_id=conversation_id, request_id=request_id
        )
        
        return error_result

async def get_pricing(
    db: AsyncSession, 
    community_id: str, 
    unit_id: str, 
    move_in_date: datetime,
    conversation_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    function_name = "get_pricing"
    arguments = {"community_id": community_id, "unit_id": unit_id, "move_in_date": move_in_date.isoformat()}
    start_time = time.time()
    
    logger.info(f"Getting pricing - Community: {community_id}, Unit: {unit_id}, Move-in: {move_in_date.date()}")
    
    try:
        pricing_repo = UnitPricingRepository()
        pricing = await pricing_repo.get_current_pricing(db, unit_id, move_in_date)
        
        if not pricing:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result = None
            logger.info(f"No pricing found - Unit: {unit_id}, Move-in: {move_in_date.date()}")
            
            await log_tool_call(
                db, function_name, arguments, {"pricing_found": False}, execution_time_ms, True,
                conversation_id=conversation_id, request_id=request_id
            )
            
            return result
        
        result = {
            "unit_id": pricing.unit_id,
            "rent": pricing.rent,
            "move_in_date": pricing.move_in_date,
            "special_offer": pricing.special_offer,
            "special_discount": pricing.special_discount,
            "effective_date": pricing.effective_date,
            "expires_date": pricing.expires_date
        }
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Pricing found - Unit: {unit_id}, Rent: ${pricing.rent}, Special: {pricing.special_offer or 'None'} in {execution_time_ms}ms")
        
        await log_tool_call(
            db, function_name, arguments, result, execution_time_ms, True,
            conversation_id=conversation_id, request_id=request_id
        )
        
        return result
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_result = {
            "unit_id": unit_id,
            "rent": 0,
            "error": str(e)
        }
        
        logger.error(f"Error getting pricing - Unit: {unit_id}, Move-in: {move_in_date.date()}, Error: {e}")
        
        await log_tool_call(
            db, function_name, arguments, error_result, execution_time_ms, False,
            error_message=str(e), conversation_id=conversation_id, request_id=request_id
        )
        
        return error_result

async def get_available_tour_slots(
    db: AsyncSession, 
    community_id: str, 
    start_date: datetime, 
    end_date: datetime,
    conversation_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    function_name = "get_available_tour_slots"
    arguments = {
        "community_id": community_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    start_time = time.time()
    
    logger.info(f"Getting available tour slots - Community: {community_id}, Range: {start_date.date()} to {end_date.date()}")
    
    try:
        tour_slot_repo = TourSlotRepository()
        available_slots = await tour_slot_repo.get_available_slots(db, community_id, start_date, end_date)
        logger.info(f"Retrieved {len(available_slots)} available tour slots")
        
        slots_data = [
            {
                "id": slot.id,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "max_capacity": slot.max_capacity,
                "current_bookings": slot.current_bookings,
                "available_spots": slot.max_capacity - slot.current_bookings,
                "is_available": slot.is_available
            }
            for slot in available_slots
        ]
        
        result = {
            "slots": slots_data,
            "total_count": len(slots_data),
            "community_id": community_id,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Tour slots lookup completed - Returning {len(slots_data)} available slots in {execution_time_ms}ms")
        
        await log_tool_call(
            db, function_name, arguments, result, execution_time_ms, True,
            conversation_id=conversation_id, request_id=request_id
        )
        
        return result
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        error_result = {
            "slots": [],
            "total_count": 0,
            "community_id": community_id,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "error": str(e)
        }
        
        logger.error(f"Error getting tour slots - Community: {community_id}, Range: {start_date.date()} to {end_date.date()}, Error: {e}")
        
        await log_tool_call(
            db, function_name, arguments, error_result, execution_time_ms, False,
            error_message=str(e), conversation_id=conversation_id, request_id=request_id
        )
        
        return error_result
