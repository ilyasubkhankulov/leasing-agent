import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from services.tools import (
    check_availability, 
    check_pet_policy, 
    get_pricing, 
    get_available_tour_slots,
    log_tool_call
)


class TestToolsService:
    
    @pytest.mark.asyncio
    async def test_check_availability_success(self, mock_db_session):
        """Test successful availability check"""
        
        mock_units = [
            MagicMock(id="unit_1", unit_number="101", bedrooms=2, bathrooms=2, square_feet=1200, is_available=True),
            MagicMock(id="unit_2", unit_number="102", bedrooms=2, bathrooms=2, square_feet=1100, is_available=True),
            MagicMock(id="unit_3", unit_number="201", bedrooms=1, bathrooms=1, square_feet=800, is_available=True)
        ]
        
        with patch('services.tools.UnitRepository') as mock_repo_class, \
             patch('services.tools.log_tool_call') as mock_log:
            
            mock_repo = AsyncMock()
            mock_repo.get_available_units.return_value = mock_units
            mock_repo_class.return_value = mock_repo
            
            result = await check_availability(mock_db_session, "community_123", 2)
            
            assert result["total_count"] == 2
            assert len(result["units"]) == 2
            assert result["units"][0]["unit_number"] == "101"
            assert result["units"][1]["unit_number"] == "102"
            assert result["bedrooms_requested"] == 2
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_availability_no_units(self, mock_db_session):
        """Test availability check when no units available"""
        
        with patch('services.tools.UnitRepository') as mock_repo_class, \
             patch('services.tools.log_tool_call') as mock_log:
            
            mock_repo = AsyncMock()
            mock_repo.get_available_units.return_value = []
            mock_repo_class.return_value = mock_repo
            
            result = await check_availability(mock_db_session, "community_123", 3)
            
            assert result["total_count"] == 0
            assert len(result["units"]) == 0
            assert result["bedrooms_requested"] == 3
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_pet_policy_success(self, mock_db_session, sample_pet_policy):
        """Test successful pet policy check"""
        
        mock_policy = MagicMock()
        mock_policy.pet_type = "dog"
        mock_policy.allowed = True
        mock_policy.deposit = 300
        mock_policy.monthly_rent = 50
        mock_policy.weight_limit = 50
        mock_policy.max_count = 2
        
        with patch('services.tools.PetPolicyRepository') as mock_repo_class, \
             patch('services.tools.log_tool_call') as mock_log:
            
            mock_repo = AsyncMock()
            mock_repo.get_by_pet_type.return_value = mock_policy
            mock_repo_class.return_value = mock_repo
            
            result = await check_pet_policy(mock_db_session, "community_123", "dog")
            
            assert result["pet_type"] == "dog"
            assert result["allowed"] is True
            assert result["deposit"] == 300
            assert result["monthly_fee"] == 50
            assert result["weight_limit"] == 50
            assert result["max_count"] == 2
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_pet_policy_not_found(self, mock_db_session):
        """Test pet policy check when policy not found"""
        
        with patch('services.tools.PetPolicyRepository') as mock_repo_class, \
             patch('services.tools.log_tool_call') as mock_log:
            
            mock_repo = AsyncMock()
            mock_repo.get_by_pet_type.return_value = None
            mock_repo_class.return_value = mock_repo
            
            result = await check_pet_policy(mock_db_session, "community_123", "bird")
            
            assert result is None
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pricing_success(self, mock_db_session):
        """Test successful pricing retrieval"""
        
        mock_pricing = MagicMock()
        mock_pricing.unit_id = "unit_1"
        mock_pricing.rent = 2500
        mock_pricing.move_in_date = datetime(2024, 3, 1)
        mock_pricing.special_offer = "First month free"
        mock_pricing.special_discount = 2500
        mock_pricing.effective_date = datetime(2024, 1, 1)
        mock_pricing.expires_date = datetime(2024, 6, 30)
        
        with patch('services.tools.UnitPricingRepository') as mock_repo_class, \
             patch('services.tools.log_tool_call') as mock_log:
            
            mock_repo = AsyncMock()
            mock_repo.get_current_pricing.return_value = mock_pricing
            mock_repo_class.return_value = mock_repo
            
            move_in_date = datetime(2024, 3, 1)
            result = await get_pricing(mock_db_session, "community_123", "unit_1", move_in_date)
            
            assert result["unit_id"] == "unit_1"
            assert result["rent"] == 2500
            assert result["special_offer"] == "First month free"
            assert result["special_discount"] == 2500
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pricing_not_found(self, mock_db_session):
        """Test pricing retrieval when no pricing found"""
        
        with patch('services.tools.UnitPricingRepository') as mock_repo_class, \
             patch('services.tools.log_tool_call') as mock_log:
            
            mock_repo = AsyncMock()
            mock_repo.get_current_pricing.return_value = None
            mock_repo_class.return_value = mock_repo
            
            move_in_date = datetime(2024, 3, 1)
            result = await get_pricing(mock_db_session, "community_123", "unit_1", move_in_date)
            
            assert result is None
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_tour_slots_success(self, mock_db_session):
        """Test successful tour slots retrieval"""
        
        mock_slots = [
            MagicMock(
                id="slot_1",
                start_time=datetime(2024, 3, 15, 10, 0),
                end_time=datetime(2024, 3, 15, 11, 0),
                max_capacity=4,
                current_bookings=1,
                is_available=True
            ),
            MagicMock(
                id="slot_2",
                start_time=datetime(2024, 3, 15, 14, 0),
                end_time=datetime(2024, 3, 15, 15, 0),
                max_capacity=4,
                current_bookings=0,
                is_available=True
            )
        ]
        
        with patch('services.tools.TourSlotRepository') as mock_repo_class, \
             patch('services.tools.log_tool_call') as mock_log:
            
            mock_repo = AsyncMock()
            mock_repo.get_available_slots.return_value = mock_slots
            mock_repo_class.return_value = mock_repo
            
            start_date = datetime(2024, 3, 15)
            end_date = datetime(2024, 3, 16)
            
            result = await get_available_tour_slots(mock_db_session, "community_123", start_date, end_date)
            
            assert result["total_count"] == 2
            assert len(result["slots"]) == 2
            assert result["slots"][0]["available_spots"] == 3
            assert result["slots"][1]["available_spots"] == 4
            mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_tool_call_success(self, mock_db_session):
        """Test successful tool call logging"""
        
        with patch('services.tools.ToolCallRepository') as mock_repo_class:
            
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo
            
            await log_tool_call(
                mock_db_session,
                "check_availability",
                {"community_id": "comm_1", "bedrooms": 2},
                {"units": [], "total_count": 0},
                150,
                True,
                conversation_id="conv_123"
            )
            
            mock_repo.create.assert_called_once()
            call_args = mock_repo.create.call_args[0]
            call_data = call_args[1]
            
            assert call_data["function_name"] == "check_availability"
            assert call_data["success"] is True
            assert call_data["execution_time_ms"] == 150

    @pytest.mark.asyncio
    async def test_error_handling_in_tools(self, mock_db_session):
        """Test error handling in tool functions"""
        
        with patch('services.tools.UnitRepository') as mock_repo_class, \
             patch('services.tools.log_tool_call') as mock_log:
            
            mock_repo = AsyncMock()
            mock_repo.get_available_units.side_effect = Exception("Database error")
            mock_repo_class.return_value = mock_repo
            
            result = await check_availability(mock_db_session, "community_123", 2)
            
            assert "error" in result
            assert result["total_count"] == 0
            mock_log.assert_called_once()
                
            # Verify error was logged
            call_args = mock_log.call_args
            # success is the 6th positional argument (index 5)
            assert call_args[0][5] is False
            # error_message is passed as keyword argument
            assert call_args[1]["error_message"] == "Database error"