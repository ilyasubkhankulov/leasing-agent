import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json
from services.llm import handle_lead_inquiry, ActionResponse


class TestLLMService:
    
    @pytest.mark.asyncio
    async def test_availability_success_scenario(self, mock_db_session, sample_inquiry_data, sample_units, mock_openai_client):
        """Test successful availability check with units found"""
        
        # Mock tool response
        with patch('services.llm.check_availability') as mock_check_availability:
            mock_check_availability.return_value = {
                "units": sample_units,
                "total_count": 2,
                "community_id": "community_123",
                "bedrooms_requested": 2
            }
            
            # Mock OpenAI responses
            with patch('services.llm.client', mock_openai_client):
                # First response with tool calls
                tool_call = MagicMock()
                tool_call.id = "call_123"
                tool_call.function.name = "check_availability"
                tool_call.function.arguments = json.dumps({
                    "community_id": "community_123",
                    "bedrooms": 2
                })
                
                first_response = MagicMock()
                first_response.tool_calls = [tool_call]
                first_response.content = None
                mock_openai_client.chat.completions.create.return_value.choices[0].message = first_response
                
                # Second response with structured output
                structured_response_content = json.dumps({
                    "response_text": "Great! I found 2 available 2-bedroom units. Unit 101 has 1200 sq ft and Unit 102 has 1100 sq ft. Would you like to schedule a tour?",
                    "action_type": "propose_tour",
                    "tour_time": "10:00",
                    "tour_date": "2024-03-15",
                    "unit_id": "unit_1",
                    "confirmation_required": True
                })
                
                # Mock the second call for structured response
                mock_openai_client.chat.completions.create.side_effect = [
                    mock_openai_client.chat.completions.create.return_value,  # First call
                    MagicMock(choices=[MagicMock(message=MagicMock(content=structured_response_content))], usage=MagicMock(total_tokens=120))  # Second call
                ]
                
                result = await handle_lead_inquiry(mock_db_session, sample_inquiry_data)
                
                assert isinstance(result, ActionResponse)
                assert result.action_type == "propose_tour"
                assert result.unit_id == "unit_1"
                assert result.tour_time == "10:00"
                assert result.tour_date == "2024-03-15"
                assert "2 available" in result.response_text
                mock_check_availability.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_availability_scenario(self, mock_db_session, sample_inquiry_data, mock_openai_client):
        """Test scenario when no units are available"""
        
        # Update inquiry for 3 bedrooms
        sample_inquiry_data["preferences"]["bedrooms"] = 3
        sample_inquiry_data["message"] = "I need a 3 bedroom apartment"
        
        with patch('services.llm.check_availability') as mock_check_availability:
            mock_check_availability.return_value = {
                "units": [],
                "total_count": 0,
                "community_id": "community_123", 
                "bedrooms_requested": 3
            }
            
            with patch('services.llm.client', mock_openai_client):
                # Mock tool call
                tool_call = MagicMock()
                tool_call.id = "call_124"
                tool_call.function.name = "check_availability"
                tool_call.function.arguments = json.dumps({
                    "community_id": "community_123",
                    "bedrooms": 3
                })
                
                first_response = MagicMock()
                first_response.tool_calls = [tool_call]
                mock_openai_client.chat.completions.create.return_value.choices[0].message = first_response
                
                # Response for no availability
                structured_response_content = json.dumps({
                    "response_text": "I'm sorry, but we don't currently have any 3-bedroom units available. Let me connect you with our leasing specialist who can help you with a waitlist or alternative options.",
                    "action_type": "handoff_human"
                })
                
                mock_openai_client.chat.completions.create.side_effect = [
                    mock_openai_client.chat.completions.create.return_value,
                    MagicMock(choices=[MagicMock(message=MagicMock(content=structured_response_content))], usage=MagicMock(total_tokens=100))
                ]
                
                result = await handle_lead_inquiry(mock_db_session, sample_inquiry_data)
                
                assert result.action_type == "handoff_human"
                assert "don't currently have any 3-bedroom" in result.response_text
                mock_check_availability.assert_called_once()

    @pytest.mark.asyncio
    async def test_pet_policy_scenario(self, mock_db_session, sample_inquiry_data, sample_pet_policy, mock_openai_client):
        """Test pet policy inquiry"""
        
        sample_inquiry_data["message"] = "Do you allow dogs? I have a 30lb golden retriever."
        
        with patch('services.llm.check_pet_policy') as mock_check_pet_policy:
            mock_check_pet_policy.return_value = sample_pet_policy
            
            with patch('services.llm.client', mock_openai_client):
                tool_call = MagicMock()
                tool_call.id = "call_125"
                tool_call.function.name = "check_pet_policy"
                tool_call.function.arguments = json.dumps({
                    "community_id": "community_123",
                    "pet_type": "dog"
                })
                
                first_response = MagicMock()
                first_response.tool_calls = [tool_call]
                mock_openai_client.chat.completions.create.return_value.choices[0].message = first_response
                
                structured_response_content = json.dumps({
                    "response_text": "Great news! We are pet-friendly and allow dogs. There's a $300 pet deposit and $50 monthly pet fee. We allow up to 2 dogs with a 50lb weight limit, so your golden retriever would be perfect!",
                    "action_type": "ask_clarification",
                    "clarification_needed": "Would you like to see available units that would work well for you and your dog?"
                })
                
                mock_openai_client.chat.completions.create.side_effect = [
                    mock_openai_client.chat.completions.create.return_value,
                    MagicMock(choices=[MagicMock(message=MagicMock(content=structured_response_content))], usage=MagicMock(total_tokens=130))
                ]
                
                result = await handle_lead_inquiry(mock_db_session, sample_inquiry_data)
                
                assert result.action_type == "ask_clarification"
                assert "$300 pet deposit" in result.response_text
                assert "$50 monthly pet fee" in result.response_text
                mock_check_pet_policy.assert_called_once()

    @pytest.mark.asyncio 
    async def test_pricing_inquiry_scenario(self, mock_db_session, sample_inquiry_data, sample_pricing, mock_openai_client):
        """Test pricing inquiry for specific unit"""
        
        sample_inquiry_data["message"] = "What's the rent for unit 101?"
        
        with patch('services.llm.get_pricing') as mock_get_pricing:
            mock_get_pricing.return_value = sample_pricing
            
            with patch('services.llm.client', mock_openai_client):
                tool_call = MagicMock()
                tool_call.id = "call_126"
                tool_call.function.name = "get_pricing"
                tool_call.function.arguments = json.dumps({
                    "community_id": "community_123",
                    "unit_id": "unit_1",
                    "move_in_date": "2024-03-01"
                })
                
                first_response = MagicMock()
                first_response.tool_calls = [tool_call]
                mock_openai_client.chat.completions.create.return_value.choices[0].message = first_response
                
                structured_response_content = json.dumps({
                    "response_text": "Unit 101 is $2,500/month, and we have a great special offer - your first month is free! That's a $2,500 savings. This offer is valid until June 30th. Would you like to schedule a tour?",
                    "action_type": "propose_tour",
                    "tour_time": "14:00",
                    "tour_date": "2024-03-10",
                    "unit_id": "unit_1",
                    "confirmation_required": True
                })
                
                mock_openai_client.chat.completions.create.side_effect = [
                    mock_openai_client.chat.completions.create.return_value,
                    MagicMock(choices=[MagicMock(message=MagicMock(content=structured_response_content))], usage=MagicMock(total_tokens=140))
                ]
                
                result = await handle_lead_inquiry(mock_db_session, sample_inquiry_data)
                
                assert result.action_type == "propose_tour"
                assert "$2,500/month" in result.response_text
                assert "first month is free" in result.response_text
                mock_get_pricing.assert_called_once()

    @pytest.mark.asyncio
    async def test_tour_confirmation_scenario(self, mock_db_session, sample_inquiry_data, mock_openai_client):
        """Test tour confirmation response"""
        
        sample_inquiry_data["message"] = "That sounds perfect! Yes, let's schedule it."
        sample_inquiry_data["conversation_history"] = [
            {"role": "user", "content": "Looking for a 2 bedroom", "timestamp": "2024-01-15T10:00:00"},
            {"role": "assistant", "content": "I found great options! Would you like a tour tomorrow at 2pm?", "timestamp": "2024-01-15T10:01:00"}
        ]
        
        with patch('services.llm.client', mock_openai_client):
            # No tool calls needed for confirmation
            first_response = MagicMock()
            first_response.tool_calls = None
            first_response.content = "Perfect! I'll confirm your tour."
            mock_openai_client.chat.completions.create.return_value.choices[0].message = first_response
            
            structured_response_content = json.dumps({
                "response_text": "Perfect! Your tour is confirmed for tomorrow at 2:00 PM. I'll send you a confirmation email with all the details. Looking forward to seeing you!",
                "action_type": "tour_confirmed"
            })
            
            mock_openai_client.chat.completions.create.side_effect = [
                mock_openai_client.chat.completions.create.return_value,
                MagicMock(choices=[MagicMock(message=MagicMock(content=structured_response_content))], usage=MagicMock(total_tokens=80))
            ]
            
            result = await handle_lead_inquiry(mock_db_session, sample_inquiry_data)
            
            assert result.action_type == "tour_confirmed"
            assert "tour is confirmed" in result.response_text
            assert len(sample_inquiry_data["conversation_history"]) == 2

    @pytest.mark.asyncio
    async def test_error_handling_scenario(self, mock_db_session, sample_inquiry_data, mock_openai_client):
        """Test error handling when tool calls fail"""
        
        with patch('services.llm.check_availability') as mock_check_availability:
            # Simulate tool failure
            mock_check_availability.side_effect = Exception("Database connection failed")
            
            with patch('services.llm.client', mock_openai_client):
                tool_call = MagicMock()
                tool_call.id = "call_127"
                tool_call.function.name = "check_availability"
                tool_call.function.arguments = json.dumps({
                    "community_id": "community_123",
                    "bedrooms": 2
                })
                
                first_response = MagicMock()
                first_response.tool_calls = [tool_call]
                mock_openai_client.chat.completions.create.return_value.choices[0].message = first_response
                
                structured_response_content = json.dumps({
                    "response_text": "I'm having trouble accessing our availability system right now. Let me connect you with a leasing specialist who can help you immediately.",
                    "action_type": "handoff_human"
                })
                
                mock_openai_client.chat.completions.create.side_effect = [
                    mock_openai_client.chat.completions.create.return_value,
                    MagicMock(choices=[MagicMock(message=MagicMock(content=structured_response_content))], usage=MagicMock(total_tokens=90))
                ]
                
                result = await handle_lead_inquiry(mock_db_session, sample_inquiry_data)
                
                assert result.action_type == "handoff_human"
                assert "trouble accessing" in result.response_text