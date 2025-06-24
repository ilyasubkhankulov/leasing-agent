import sys
import os
from pathlib import Path

# Add the app directory to Python path so modules can be found without 'app.' prefix
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def sample_lead():
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-0123"
    }


@pytest.fixture
def sample_preferences():
    return {
        "bedrooms": 2,
        "move_in": "2024-03-01"
    }


@pytest.fixture
def sample_inquiry_data(sample_lead, sample_preferences):
    return {
        "lead": sample_lead,
        "message": "Hi, I'm looking for a 2 bedroom apartment",
        "conversation_history": [],
        "preferences": sample_preferences,
        "community_id": "community_123"
    }


@pytest.fixture
def sample_units():
    return [
        {
            "id": "unit_1",
            "unit_number": "101",
            "bedrooms": 2,
            "bathrooms": 2,
            "square_feet": 1200,
            "is_available": True
        },
        {
            "id": "unit_2", 
            "unit_number": "102",
            "bedrooms": 2,
            "bathrooms": 2,
            "square_feet": 1100,
            "is_available": True
        }
    ]


@pytest.fixture
def sample_pet_policy():
    return {
        "pet_type": "dog",
        "allowed": True,
        "deposit": 300,
        "monthly_fee": 50,
        "weight_limit": 50,
        "max_count": 2
    }


@pytest.fixture
def sample_pricing():
    return {
        "unit_id": "unit_1",
        "rent": 2500,
        "move_in_date": datetime(2024, 3, 1),
        "special_offer": "First month free",
        "special_discount": 2500,
        "effective_date": datetime(2024, 1, 1),
        "expires_date": datetime(2024, 6, 30)
    }


@pytest.fixture
def mock_openai_client():
    mock_client = MagicMock()
    
    # Mock response structure
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.usage.total_tokens = 150
    
    mock_client.chat.completions.create.return_value = mock_response
    
    return mock_client
