"""MCP Client for connecting to MCP servers"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json
import requests
from pathlib import Path


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    url: str
    api_key: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True
    timeout: int = 30
    headers: Optional[Dict[str, str]] = None


class MCPClient:
    """Client for interacting with MCP servers"""

    def __init__(self, config: MCPServerConfig):
        """
        Initialize MCP client

        Args:
            config: Server configuration
        """
        self.config = config
        self.session = requests.Session()

        # Set up headers
        self.session.headers.update({
            "Content-Type": "application/json",
        })

        if config.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {config.api_key}"
            })

        if config.headers:
            self.session.headers.update(config.headers)

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server

        Returns:
            List of tool definitions
        """
        try:
            response = self.session.get(
                f"{self.config.url}/tools",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json().get("tools", [])
        except Exception as e:
            raise ConnectionError(f"Failed to list tools from {self.config.name}: {e}")

    def list_resources(self) -> List[Dict[str, Any]]:
        """
        List available resources from the MCP server

        Returns:
            List of resource definitions
        """
        try:
            response = self.session.get(
                f"{self.config.url}/resources",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json().get("resources", [])
        except Exception as e:
            raise ConnectionError(f"Failed to list resources from {self.config.name}: {e}")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        try:
            payload = {
                "tool": tool_name,
                "arguments": arguments
            }

            response = self.session.post(
                f"{self.config.url}/tools/call",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to call tool {tool_name} on {self.config.name}: {e}")

    def get_resource(self, resource_uri: str) -> Any:
        """
        Get a resource from the MCP server

        Args:
            resource_uri: URI of the resource

        Returns:
            Resource content
        """
        try:
            response = self.session.get(
                f"{self.config.url}/resources/{resource_uri}",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to get resource {resource_uri} from {self.config.name}: {e}")

    def health_check(self) -> bool:
        """
        Check if the MCP server is healthy

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.config.url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information

        Returns:
            Server info dict
        """
        try:
            response = self.session.get(
                f"{self.config.url}/info",
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "name": self.config.name,
                "status": "error",
                "error": str(e)
            }
