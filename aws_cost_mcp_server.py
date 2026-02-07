"""
AWS Cost MCP Server.
Exposes AWS cost management tools via the Model Context Protocol.
"""
from flask import Flask, request, jsonify
from typing import Dict, Any, List
import logging

from aws_cost_service import AWSCostService
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
cost_service = AWSCostService()


# Tool definitions
TOOLS = [
    {
        "name": "get_cost_and_usage",
        "description": "Retrieve AWS cost and usage data for a specified time period",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                },
                "granularity": {
                    "type": "string",
                    "enum": ["DAILY", "MONTHLY", "HOURLY"],
                    "description": "Time granularity for the data",
                    "default": "DAILY"
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_cost_forecast",
        "description": "Get cost forecasts for future periods",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                },
                "metric": {
                    "type": "string",
                    "description": "Forecast metric",
                    "default": "UNBLENDED_COST"
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_cost_anomalies",
        "description": "Detect unusual spending patterns and cost anomalies",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of anomalies to return",
                    "default": 100
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_service_costs",
        "description": "Break down costs by AWS service",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format"
                }
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "get_optimization_recommendations",
        "description": "Fetch AWS Cost Explorer optimization recommendations",
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of recommendations to return",
                    "default": 100
                }
            }
        }
    }
]


@app.route('/tools', methods=['GET'])
def list_tools():
    """List all available tools."""
    return jsonify({'tools': TOOLS})


@app.route('/invoke', methods=['POST'])
def invoke_tool():
    """Invoke a specific tool."""
    try:
        data = request.get_json()
        tool_name = data.get('tool')
        parameters = data.get('parameters', {})
        
        logger.info(f"Invoking tool: {tool_name} with parameters: {parameters}")
        
        # Route to appropriate handler
        if tool_name == 'get_cost_and_usage':
            result = cost_service.get_cost_and_usage(**parameters)
        elif tool_name == 'get_cost_forecast':
            result = cost_service.get_cost_forecast(**parameters)
        elif tool_name == 'get_cost_anomalies':
            result = cost_service.get_cost_anomalies(**parameters)
        elif tool_name == 'get_service_costs':
            result = cost_service.get_service_costs(**parameters)
        elif tool_name == 'get_optimization_recommendations':
            result = cost_service.get_optimization_recommendations(**parameters)
        else:
            return jsonify({
                'error': f'Unknown tool: {tool_name}'
            }), 400
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        logger.error(f"Error invoking tool: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


def main():
    """Start the MCP server."""
    logger.info(f"Starting AWS Cost MCP Server on {Config.MCP_SERVER_HOST}:{Config.MCP_SERVER_PORT}")
    app.run(
        host=Config.MCP_SERVER_HOST,
        port=Config.MCP_SERVER_PORT,
        debug=(Config.LOG_LEVEL == 'DEBUG')
    )


if __name__ == '__main__':
    main()
