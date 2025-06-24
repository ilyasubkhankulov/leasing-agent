from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from db.repository import UnitRepository, PetPolicyRepository, UnitPricingRepository

async def check_availability(db: AsyncSession, community_id: str, bedrooms: int) -> List[Dict[str, Any]]:
    unit_repo = UnitRepository()
    
    available_units = await unit_repo.get_available_units(db, community_id)
    
    filtered_units = [
        unit for unit in available_units 
        if unit.bedrooms == bedrooms
    ]
    
    return [
        {
            "id": unit.id,
            "unit_number": unit.unit_number,
            "bedrooms": unit.bedrooms,
            "bathrooms": unit.bathrooms,
            "square_feet": unit.square_feet,
            "floor": unit.floor,
            "is_available": unit.is_available
        }
        for unit in filtered_units
    ]

async def check_pet_policy(db: AsyncSession, community_id: str, pet_type: str) -> Optional[Dict[str, Any]]:
    pet_policy_repo = PetPolicyRepository()
    
    policy = await pet_policy_repo.get_by_pet_type(db, community_id, pet_type)
    
    if not policy:
        return None
    
    return {
        "pet_type": policy.pet_type,
        "allowed": policy.allowed,
        "deposit": policy.deposit,
        "monthly_fee": policy.monthly_fee,
        "weight_limit": policy.weight_limit,
        "breed_restrictions": policy.breed_restrictions
    }

async def get_pricing(db: AsyncSession, community_id: str, unit_id: str, move_in_date: datetime) -> Optional[Dict[str, Any]]:
    pricing_repo = UnitPricingRepository()
    
    pricing = await pricing_repo.get_current_pricing(db, unit_id, move_in_date)
    
    if not pricing:
        return None
    
    return {
        "unit_id": pricing.unit_id,
        "monthly_rent": pricing.monthly_rent,
        "security_deposit": pricing.security_deposit,
        "admin_fee": pricing.admin_fee,
        "move_in_date": pricing.move_in_date,
        "lease_term": pricing.lease_term,
        "special_offer": pricing.special_offer,
        "effective_date": pricing.effective_date,
        "expires_date": pricing.expires_date
    }
