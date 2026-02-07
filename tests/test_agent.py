"""
Tests for Agent Orchestrator.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from agent_orchestrator import AgentOrchestrator


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client."""
    with patch('agent_orchestrator.MCPClient') as mock:
        client = Mock()
        client.discover_tools.return_value = [
            {
                'name': 'get_cost_and_usage',
                'description': 'Get cost and usage data',
                'parameters': {'type': 'object', 'properties': {}}
            }
        ]
        client.invoke_tool.return_value = {
            'success': True,
            'result': {'Total': {'Amount': '100.00'}}
        }
        mock.return_value = client
        yield client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch('agent_orchestrator.OpenAI') as mock:
        client = Mock()
        
        # Mock response without tool calls
        response = Mock()
        response.choices = [Mock()]
        response.choices[0].message.content = "Your AWS costs were $100 last month."
        response.choices[0].message.tool_calls = None
        
        client.return_value.chat.completions.create.return_value = response
        mock.return_value = client
        yield client


def test_agent_initialization(mock_mcp_client):
    """Test agent initialization."""
    with patch('agent_orchestrator.OpenAI'):
        agent = AgentOrchestrator(llm_provider='openai')
        assert agent.llm_provider == 'openai'
        assert len(agent.available_tools) == 1


def test_format_tools_for_llm(mock_mcp_client):
    """Test tool formatting for LLM."""
    with patch('agent_orchestrator.OpenAI'):
        agent = AgentOrchestrator(llm_provider='openai')
        formatted = agent._format_tools_for_llm()
        
        assert len(formatted) == 1
        assert formatted[0]['type'] == 'function'
        assert 'function' in formatted[0]
        assert formatted[0]['function']['name'] == 'get_cost_and_usage'


def test_process_query_openai(mock_mcp_client, mock_openai_client):
    """Test processing query with OpenAI."""
    agent = AgentOrchestrator(llm_provider='openai')
    
    response = agent.process_query("What were my costs last month?")
    
    assert isinstance(response, str)
    assert len(response) > 0


def test_process_query_with_tool_calls(mock_mcp_client):
    """Test processing query that requires tool calls."""
    with patch('agent_orchestrator.OpenAI') as mock_openai:
        # First response: tool call
        tool_call_response = Mock()
        tool_call_response.choices = [Mock()]
        tool_call_response.choices[0].message.content = None
        tool_call_response.choices[0].message.tool_calls = [Mock()]
        tool_call_response.choices[0].message.tool_calls[0].id = 'call_123'
        tool_call_response.choices[0].message.tool_calls[0].function.name = 'get_cost_and_usage'
        tool_call_response.choices[0].message.tool_calls[0].function.arguments = '{"start_date": "2024-01-01", "end_date": "2024-01-31"}'
        
        # Second response: final answer
        final_response = Mock()
        final_response.choices = [Mock()]
        final_response.choices[0].message.content = "Your costs were $100."
        final_response.choices[0].message.tool_calls = None
        
        client = Mock()
        client.chat.completions.create.side_effect = [tool_call_response, final_response]
        mock_openai.return_value = client
        
        agent = AgentOrchestrator(llm_provider='openai')
        response = agent.process_query("What were my costs?")
        
        assert "costs" in response.lower()
        mock_mcp_client.invoke_tool.assert_called_once()


def test_unsupported_llm_provider():
    """Test initialization with unsupported LLM provider."""
    with pytest.raises(ValueError):
        AgentOrchestrator(llm_provider='unsupported')


def test_agent_close(mock_mcp_client):
    """Test agent cleanup."""
    with patch('agent_orchestrator.OpenAI'):
        agent = AgentOrchestrator(llm_provider='openai')
        agent.close()
        
        mock_mcp_client.close.assert_called_once()
