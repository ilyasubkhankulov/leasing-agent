from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from db.repository import UnitRepository, PetPolicyRepository, UnitPricingRepository
from core.logging import get_logger

logger = get_logger(__name__)

async def check_availability(db: AsyncSession, community_id: str, bedrooms: int) -> Dict[str, Any]:
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
        
        logger.info(f"Availability check completed - Returning {len(units_data)} matching units")
        return result
        
    except Exception as e:
        logger.error(f"Error checking availability - Community: {community_id}, Bedrooms: {bedrooms}, Error: {e}")
        return {
            "units": [],
            "total_count": 0,
            "community_id": community_id,
            "bedrooms_requested": bedrooms,
            "error": str(e)
        }

async def check_pet_policy(db: AsyncSession, community_id: str, pet_type: str) -> Optional[Dict[str, Any]]:
    logger.info(f"Checking pet policy - Community: {community_id}, Pet type: {pet_type}")
    
    try:
        pet_policy_repo = PetPolicyRepository()
        policy = await pet_policy_repo.get_by_pet_type(db, community_id, pet_type)
        
        if not policy:
            logger.info(f"No pet policy found - Community: {community_id}, Pet type: {pet_type}")
            return None
        
        result = {
            "pet_type": policy.pet_type,
            "allowed": policy.allowed,
            "deposit": policy.deposit,
            "monthly_fee": policy.monthly_rent,
            "weight_limit": policy.weight_limit,
            "max_count": policy.max_count
        }
        
        logger.info(f"Pet policy found - Community: {community_id}, Pet type: {pet_type}, Allowed: {policy.allowed}")
        return result
        
    except Exception as e:
        logger.error(f"Error checking pet policy - Community: {community_id}, Pet type: {pet_type}, Error: {e}")
        return {
            "pet_type": pet_type,
            "allowed": False,
            "error": str(e)
        }

async def get_pricing(db: AsyncSession, community_id: str, unit_id: str, move_in_date: datetime) -> Optional[Dict[str, Any]]:
    logger.info(f"Getting pricing - Community: {community_id}, Unit: {unit_id}, Move-in: {move_in_date.date()}")
    
    try:
        pricing_repo = UnitPricingRepository()
        pricing = await pricing_repo.get_current_pricing(db, unit_id, move_in_date)
        
        if not pricing:
            logger.info(f"No pricing found - Unit: {unit_id}, Move-in: {move_in_date.date()}")
            return None
        
        result = {
            "unit_id": pricing.unit_id,
            "rent": pricing.rent,
            "move_in_date": pricing.move_in_date,
            "special_offer": pricing.special_offer,
            "special_discount": pricing.special_discount,
            "effective_date": pricing.effective_date,
            "expires_date": pricing.expires_date
        }
        
        logger.info(f"Pricing found - Unit: {unit_id}, Rent: ${pricing.rent}, Special: {pricing.special_offer or 'None'}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting pricing - Unit: {unit_id}, Move-in: {move_in_date.date()}, Error: {e}")
        return {
            "unit_id": unit_id,
            "rent": 0,
            "error": str(e)
        }
