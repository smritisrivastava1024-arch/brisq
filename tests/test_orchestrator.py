import pytest
from unittest.mock import AsyncMock, MagicMock
from orchestrator import classify_intent, route_message

@pytest.fixture
def mock_client():
    client = MagicMock()
    # Mock AsyncGroq behavior: chat.completions.create is async and returns an object with choices
    client.chat.completions.create = AsyncMock()
    return client

@pytest.mark.asyncio
async def test_classify_intent_valid_json(mock_client):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"agents": ["customer_ai"]}'))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    agents = await classify_intent("Where is my order?", mock_client, "dummy-model")
    assert agents == ["customer_ai"]

@pytest.mark.asyncio
async def test_classify_intent_invalid_json(mock_client):
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='not valid json'))
    ]
    mock_client.chat.completions.create.return_value = mock_response

    agents = await classify_intent("Where is my order?", mock_client, "dummy-model")
    assert agents == []

@pytest.mark.asyncio
async def test_route_message_single_agent(mock_client):
    # Setup classify_intent to return a single agent
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"agents": ["customer_ai"]}'))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    
    agent_functions = {
        "customer_ai": AsyncMock(return_value="Customer response")
    }
    
    result = await route_message("Where is my order?", mock_client, "dummy-model", agent_functions)
    
    assert result["agents_used"] == ["customer_ai"]
    assert result["reply"] == "Customer response"
    agent_functions["customer_ai"].assert_called_once_with("Where is my order?")

@pytest.mark.asyncio
async def test_route_message_multi_agent(mock_client):
    # First call is for classify_intent
    mock_classify = MagicMock()
    mock_classify.message.content = '{"agents": ["customer_ai", "finance_ai"]}'
    
    # Second call is for merge_answers
    mock_merge = MagicMock()
    mock_merge.message.content = "Merged response"
    
    mock_response_1 = MagicMock(choices=[mock_classify])
    mock_response_2 = MagicMock(choices=[mock_merge])
    
    mock_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]
    
    agent_functions = {
        "customer_ai": AsyncMock(return_value="Customer response"),
        "finance_ai": AsyncMock(return_value="Finance response")
    }
    
    result = await route_message("Order and finance?", mock_client, "dummy-model", agent_functions)
    
    assert result["agents_used"] == ["customer_ai", "finance_ai"]
    assert result["reply"] == "Merged response"
    agent_functions["customer_ai"].assert_called_once_with("Order and finance?")
    agent_functions["finance_ai"].assert_called_once_with("Order and finance?")
