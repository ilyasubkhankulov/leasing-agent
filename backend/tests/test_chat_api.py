import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx
from datetime import datetime
from main import app
from api.v1.chat import StartChatRequest, ReplyRequest, Lead, Preferences


class TestChatAPI:
    
    @pytest.mark.asyncio
    async def test_get_communities_success(self):
        """Test successful retrieval of communities"""
        
        # Create simple mock objects that behave like community models
        class MockCommunity:
            def __init__(self, id, name, address, phone, email):
                self.id = id
                self.name = name
                self.address = address
                self.phone = phone
                self.email = email
        
        mock_communities = [
            MockCommunity("comm_1", "Sunset Gardens", "123 Main St", "555-0100", "info@sunset.com"),
            MockCommunity("comm_2", "Oak Valley", "456 Oak Ave", "555-0200", "info@oakvalley.com")
        ]
        
        with patch('api.v1.chat.CommunityRepository') as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = mock_communities
            mock_repo_class.return_value = mock_repo
            
            with patch('api.v1.chat.get_db_session') as mock_get_db:
                mock_get_db.return_value = AsyncMock()
                
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.get("/api/v1/chat/communities")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert len(data) == 2
                    assert data[0]["name"] == "Sunset Gardens"
                    assert data[1]["name"] == "Oak Valley"

    @pytest.mark.asyncio
    async def test_start_chat_success(self):
        """Test successful chat initiation"""
        
        mock_lead = MagicMock()
        mock_lead.id = "lead_123"
        mock_lead.name = "John Doe"
        mock_lead.email = "john@example.com"
        
        mock_conversation = MagicMock()
        mock_conversation.id = "conv_456"
        
        request_data = {
            "lead": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-0123"
            },
            "preferences": {
                "bedrooms": 2,
                "move_in": "2024-03-01"
            },
            "community_id": "community_123"
        }
        
        with patch('api.v1.chat.LeadRepository') as mock_lead_repo_class, \
             patch('api.v1.chat.ConversationRepository') as mock_conv_repo_class, \
             patch('api.v1.chat.get_db_session') as mock_get_db:
            
            mock_lead_repo = AsyncMock()
            mock_lead_repo.create_or_get_by_email.return_value = mock_lead
            mock_lead_repo_class.return_value = mock_lead_repo
            
            mock_conv_repo = AsyncMock()
            mock_conv_repo.create.return_value = mock_conversation
            mock_conv_repo_class.return_value = mock_conv_repo
            
            mock_get_db.return_value = AsyncMock()
            
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/v1/chat/start", json=request_data)
                
                assert response.status_code == 200
                data = response.json()
                assert data["lead_id"] == "lead_123"
                assert data["conversation_id"] == "conv_456"
                assert "John" in data["message"]
                assert "2-bedroom" in data["message"]

    @pytest.mark.asyncio
    async def test_reply_stream_availability_success(self):
        """Test streaming reply with availability check"""
        
        mock_lead = MagicMock()
        mock_lead.id = "lead_123"
        mock_lead.name = "John Doe"
        mock_lead.email = "john@example.com"
        mock_lead.preferred_bedrooms = 2
        mock_lead.preferred_move_in = datetime(2024, 3, 1)
        
        mock_conversation = MagicMock()
        mock_conversation.id = "conv_456"
        mock_conversation.community_id = "community_123"
        
        mock_message = MagicMock()
        mock_message.id = "msg_789"
        
        with patch('api.v1.chat.get_db_context') as mock_get_db_context, \
             patch('api.v1.chat.LeadRepository') as mock_lead_repo_class, \
             patch('api.v1.chat.ConversationRepository') as mock_conv_repo_class, \
             patch('api.v1.chat.MessageRepository') as mock_msg_repo_class, \
             patch('api.v1.chat.handle_lead_inquiry') as mock_handle_inquiry:
            
            # Mock database context
            mock_db = AsyncMock()
            mock_get_db_context.return_value.__aenter__.return_value = mock_db
            
            # Mock repositories
            mock_lead_repo = AsyncMock()
            mock_lead_repo.get_by_id.return_value = mock_lead
            mock_lead_repo_class.return_value = mock_lead_repo
            
            mock_conv_repo = AsyncMock()
            mock_conv_repo.get_by_id.return_value = mock_conversation
            mock_conv_repo_class.return_value = mock_conv_repo
            
            mock_msg_repo = AsyncMock()
            mock_msg_repo.get_by_conversation_id.return_value = []
            mock_msg_repo.create.return_value = mock_message
            mock_msg_repo_class.return_value = mock_msg_repo
            
            # Mock LLM response
            from services.llm import ActionResponse
            mock_response = ActionResponse(
                action_type="propose_tour",
                response_text="I found 2 great 2-bedroom units! Would you like to tour unit 101 tomorrow at 2 PM?",
                tour_time="14:00",
                tour_date="2024-03-16",
                unit_id="unit_1",
                confirmation_required=True,
                tokens_used=150
            )
            mock_handle_inquiry.return_value = mock_response
            
            request_data = {
                "lead_id": "lead_123",
                "conversation_id": "conv_456", 
                "message": "Show me available 2 bedroom apartments"
            }
            
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/v1/chat/reply", json=request_data)
                
                assert response.status_code == 200
                
                # Check that we get streaming response
                content = response.content.decode()
                assert "data:" in content
                
                # Verify repositories were called
                mock_lead_repo.get_by_id.assert_called_once_with(mock_db, "lead_123")
                mock_conv_repo.get_by_id.assert_called_once_with(mock_db, "conv_456")
                mock_msg_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_reply_stream_error_handling(self):
        """Test error handling in streaming reply"""
        
        with patch('api.v1.chat.get_db_context') as mock_get_db_context, \
             patch('api.v1.chat.LeadRepository') as mock_lead_repo_class:
            
            mock_db = AsyncMock()
            mock_get_db_context.return_value.__aenter__.return_value = mock_db
            
            # Mock lead not found scenario
            mock_lead_repo = AsyncMock()
            mock_lead_repo.get_by_id.return_value = None
            mock_lead_repo_class.return_value = mock_lead_repo
            
            request_data = {
                "lead_id": "invalid_lead",
                "conversation_id": "conv_456",
                "message": "Test message"
            }
            
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/v1/chat/reply", json=request_data)
                
                assert response.status_code == 200
                content = response.content.decode()
                assert "error" in content.lower()

    def test_start_chat_request_validation(self):
        """Test request validation for start chat"""
        
        # Test with missing required fields
        invalid_request = {
            "lead": {
                "name": "John Doe"
                # missing email
            },
            "preferences": {
                "bedrooms": 2,
                "move_in": "2024-03-01"
            },
            "community_id": "community_123"
        }
        
        with TestClient(app) as client:
            response = client.post("/api/v1/chat/start", json=invalid_request)
            assert response.status_code == 422  # Validation error

    def test_reply_request_validation(self):
        """Test request validation for reply"""
        
        invalid_request = {
            "lead_id": "lead_123",
            # missing conversation_id and message
        }
        
        with TestClient(app) as client:
            response = client.post("/api/v1/chat/reply", json=invalid_request)
            assert response.status_code == 422  # Validation error
