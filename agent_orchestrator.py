"""
LLM Agent Orchestrator with MCP Client.
Processes natural language queries about AWS costs and generates reports.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from anthropic import Anthropic
import httpx

from mcp_client import MCPClient
from config import Config

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """LLM agent that orchestrates AWS cost analysis using MCP tools."""
    
    def __init__(self, llm_provider: Optional[str] = None):
        """
        Initialize the agent orchestrator.
        
        Args:
            llm_provider: LLM provider to use (openai, anthropic, or ollama)
        """
        self.llm_provider = llm_provider or Config.DEFAULT_LLM_PROVIDER
        self.mcp_client = MCPClient(Config.get_mcp_server_url())
        
        # Initialize LLM client
        if self.llm_provider == 'openai':
            self.llm_client = OpenAI(api_key=Config.OPENAI_API_KEY)
            self.model = "gpt-4-turbo-preview"
        elif self.llm_provider == 'anthropic':
            self.llm_client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            self.model = "claude-3-sonnet-20240229"
        elif self.llm_provider == 'ollama':
            self.llm_client = httpx.Client(base_url=Config.OLLAMA_BASE_URL)
            self.model = Config.OLLAMA_MODEL
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        
        # Discover available tools
        self.available_tools = self.mcp_client.discover_tools()
        logger.info(f"Initialized agent with {len(self.available_tools)} tools")
    
    def _format_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Format MCP tools for LLM function calling."""
        formatted_tools = []
        for tool in self.available_tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return formatted_tools
    
    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Any:
        """
        Call the configured LLM.
        
        Args:
            messages: Conversation messages
            tools: Available tools for function calling
        
        Returns:
            LLM response
        """
        if self.llm_provider == 'openai':
            kwargs = {"model": self.model, "messages": messages}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            return self.llm_client.chat.completions.create(**kwargs)
        
        elif self.llm_provider == 'anthropic':
            kwargs = {"model": self.model, "messages": messages, "max_tokens": 4096}
            if tools:
                kwargs["tools"] = [t["function"] for t in tools]
            return self.llm_client.messages.create(**kwargs)
        
        elif self.llm_provider == 'ollama':
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }
            if tools:
                payload["tools"] = [t["function"] for t in tools]
            
            response = self.llm_client.post("/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
    
    def _extract_response_content(self, response: Any) -> str:
        """Extract text content from LLM response."""
        if self.llm_provider == 'openai':
            return response.choices[0].message.content or ""
        elif self.llm_provider == 'anthropic':
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text
            return ""
        elif self.llm_provider == 'ollama':
            return response.get('message', {}).get('content', '')
    
    def _extract_tool_calls(self, response: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response."""
        tool_calls = []
        
        if self.llm_provider == 'openai':
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    tool_calls.append({
                        'id': tool_call.id,
                        'name': tool_call.function.name,
                        'arguments': json.loads(tool_call.function.arguments)
                    })
        
        elif self.llm_provider == 'anthropic':
            for block in response.content:
                if hasattr(block, 'type') and block.type == 'tool_use':
                    tool_calls.append({
                        'id': block.id,
                        'name': block.name,
                        'arguments': block.input
                    })
        
        elif self.llm_provider == 'ollama':
            message = response.get('message', {})
            if 'tool_calls' in message:
                for tool_call in message['tool_calls']:
                    tool_calls.append({
                        'id': tool_call.get('id', ''),
                        'name': tool_call['function']['name'],
                        'arguments': tool_call['function']['arguments']
                    })
        
        return tool_calls
    
    def process_query(self, query: str) -> str:
        """
        Process a natural language query about AWS costs.
        
        Args:
            query: User's question about AWS costs
        
        Returns:
            Human-readable response
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AWS cost analysis assistant. You have access to tools that can "
                    "retrieve AWS cost data, forecasts, anomalies, and optimization recommendations. "
                    "Use these tools to answer user questions about AWS costs. Provide clear, "
                    "actionable insights and recommendations."
                )
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        tools = self._format_tools_for_llm()
        max_iterations = 5
        
        for iteration in range(max_iterations):
            logger.info(f"LLM iteration {iteration + 1}/{max_iterations}")
            
            # Call LLM
            response = self._call_llm(messages, tools)
            
            # Check for tool calls
            tool_calls = self._extract_tool_calls(response)
            
            if not tool_calls:
                # No more tool calls, return final response
                return self._extract_response_content(response)
            
            # Execute tool calls
            for tool_call in tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['arguments']
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                
                try:
                    result = self.mcp_client.invoke_tool(tool_name, tool_args)
                    tool_result = json.dumps(result, indent=2)
                except Exception as e:
                    tool_result = f"Error executing tool: {str(e)}"
                    logger.error(f"Tool execution error: {e}")
                
                # Add tool result to messages
                if self.llm_provider == 'openai':
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tool_call['id'],
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_args)
                            }
                        }]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "content": tool_result
                    })
                elif self.llm_provider == 'anthropic':
                    messages.append({
                        "role": "assistant",
                        "content": [{
                            "type": "tool_use",
                            "id": tool_call['id'],
                            "name": tool_name,
                            "input": tool_args
                        }]
                    })
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_call['id'],
                            "content": tool_result
                        }]
                    })
                elif self.llm_provider == 'ollama':
                    messages.append({
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [{
                            "function": {
                                "name": tool_name,
                                "arguments": tool_args
                            }
                        }]
                    })
                    messages.append({
                        "role": "tool",
                        "content": tool_result
                    })
        
        return "Maximum iterations reached. Please try a simpler query."
    
    def close(self):
        """Clean up resources."""
        self.mcp_client.close()
        if self.llm_provider == 'ollama':
            self.llm_client.close()


def main():
    """Example usage of the agent orchestrator."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python agent_orchestrator.py <query>")
        print("Example: python agent_orchestrator.py 'What were my AWS costs last month?'")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    
    agent = AgentOrchestrator()
    try:
        response = agent.process_query(query)
        print("\n" + "="*80)
        print("RESPONSE:")
        print("="*80)
        print(response)
        print("="*80)
    finally:
        agent.close()


if __name__ == '__main__':
    main()
