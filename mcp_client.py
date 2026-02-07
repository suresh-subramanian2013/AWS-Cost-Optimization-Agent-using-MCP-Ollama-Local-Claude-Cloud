"""
MCP Protocol Client Implementation.
Handles communication with MCP servers, tool discovery, and invocation.
"""
import httpx
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """Model Context Protocol client for communicating with MCP servers."""
    
    def __init__(self, server_url: str):
        """
        Initialize MCP client.
        
        Args:
            server_url: Base URL of the MCP server
        """
        self.server_url = server_url.rstrip('/')
        self.client = httpx.Client(timeout=30.0)
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
    
    def discover_tools(self) -> List[Dict[str, Any]]:
        """
        Discover available tools from the MCP server.
        
        Returns:
            List of tool definitions
        """
        try:
            response = self.client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            self._tools_cache = response.json().get('tools', [])
            logger.info(f"Discovered {len(self._tools_cache)} tools from MCP server")
            return self._tools_cache
        except httpx.HTTPError as e:
            logger.error(f"Error discovering tools: {e}")
            raise
    
    def get_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get definition for a specific tool.
        
        Args:
            tool_name: Name of the tool
        
        Returns:
            Tool definition or None if not found
        """
        if self._tools_cache is None:
            self.discover_tools()
        
        for tool in self._tools_cache:
            if tool.get('name') == tool_name:
                return tool
        
        return None
    
    def invoke_tool(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to invoke
            parameters: Tool parameters
        
        Returns:
            Tool execution result
        """
        if parameters is None:
            parameters = {}
        
        try:
            payload = {
                'tool': tool_name,
                'parameters': parameters
            }
            
            response = self.client.post(
                f"{self.server_url}/invoke",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Successfully invoked tool: {tool_name}")
            return result
        except httpx.HTTPError as e:
            logger.error(f"Error invoking tool {tool_name}: {e}")
            raise
    
    def get_available_tools(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List of tool names
        """
        if self._tools_cache is None:
            self.discover_tools()
        
        return [tool.get('name') for tool in self._tools_cache]
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
