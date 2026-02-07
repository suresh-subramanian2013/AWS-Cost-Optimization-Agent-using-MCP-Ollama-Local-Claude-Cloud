"""
Tests for AWS Cost MCP Server.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from aws_cost_mcp_server import app, TOOLS


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_list_tools(client):
    """Test tool listing endpoint."""
    response = client.get('/tools')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'tools' in data
    assert len(data['tools']) == 5
    
    tool_names = [tool['name'] for tool in data['tools']]
    assert 'get_cost_and_usage' in tool_names
    assert 'get_cost_forecast' in tool_names
    assert 'get_cost_anomalies' in tool_names
    assert 'get_service_costs' in tool_names
    assert 'get_optimization_recommendations' in tool_names


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'


@patch('aws_cost_mcp_server.cost_service')
def test_invoke_get_cost_and_usage(mock_cost_service, client):
    """Test invoking get_cost_and_usage tool."""
    mock_result = {
        'ResultsByTime': [
            {
                'TimePeriod': {'Start': '2024-01-01', 'End': '2024-01-02'},
                'Total': {'UnblendedCost': {'Amount': '100.50', 'Unit': 'USD'}}
            }
        ]
    }
    mock_cost_service.get_cost_and_usage.return_value = mock_result
    
    response = client.post('/invoke', json={
        'tool': 'get_cost_and_usage',
        'parameters': {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'granularity': 'DAILY'
        }
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'result' in data
    
    mock_cost_service.get_cost_and_usage.assert_called_once_with(
        start_date='2024-01-01',
        end_date='2024-01-31',
        granularity='DAILY'
    )


@patch('aws_cost_mcp_server.cost_service')
def test_invoke_get_cost_forecast(mock_cost_service, client):
    """Test invoking get_cost_forecast tool."""
    mock_result = {
        'Total': {'Amount': '500.00', 'Unit': 'USD'},
        'ForecastResultsByTime': []
    }
    mock_cost_service.get_cost_forecast.return_value = mock_result
    
    response = client.post('/invoke', json={
        'tool': 'get_cost_forecast',
        'parameters': {
            'start_date': '2024-02-01',
            'end_date': '2024-02-29'
        }
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True


@patch('aws_cost_mcp_server.cost_service')
def test_invoke_unknown_tool(mock_cost_service, client):
    """Test invoking an unknown tool."""
    response = client.post('/invoke', json={
        'tool': 'unknown_tool',
        'parameters': {}
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


@patch('aws_cost_mcp_server.cost_service')
def test_invoke_tool_error(mock_cost_service, client):
    """Test tool invocation error handling."""
    mock_cost_service.get_cost_and_usage.side_effect = Exception("AWS API Error")
    
    response = client.post('/invoke', json={
        'tool': 'get_cost_and_usage',
        'parameters': {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
    })
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data
