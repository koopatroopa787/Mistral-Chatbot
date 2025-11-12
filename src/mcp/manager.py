"""MCP Manager for managing multiple MCP server connections"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from .client import MCPClient, MCPServerConfig


class MCPManager:
    """Manager for MCP server connections"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize MCP manager

        Args:
            config_path: Path to MCP configuration file
        """
        self.clients: Dict[str, MCPClient] = {}
        self.config_path = config_path or Path("config/mcp_servers.json")

        # Load configurations
        if self.config_path.exists():
            self.load_configs()

    def load_configs(self):
        """Load MCP server configurations from file"""
        try:
            with open(self.config_path, 'r') as f:
                configs_data = json.load(f)

            for config_data in configs_data.get("servers", []):
                config = MCPServerConfig(**config_data)
                if config.enabled:
                    self.add_server(config)
        except Exception as e:
            print(f"Error loading MCP configs: {e}")

    def save_configs(self):
        """Save MCP server configurations to file"""
        configs_data = {
            "servers": [
                {
                    "name": client.config.name,
                    "url": client.config.url,
                    "api_key": client.config.api_key,
                    "description": client.config.description,
                    "enabled": client.config.enabled,
                    "timeout": client.config.timeout,
                    "headers": client.config.headers,
                }
                for client in self.clients.values()
            ]
        }

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(configs_data, f, indent=2)

    def add_server(self, config: MCPServerConfig) -> MCPClient:
        """
        Add an MCP server

        Args:
            config: Server configuration

        Returns:
            MCP client instance
        """
        client = MCPClient(config)
        self.clients[config.name] = client
        return client

    def remove_server(self, name: str):
        """
        Remove an MCP server

        Args:
            name: Server name
        """
        if name in self.clients:
            del self.clients[name]

    def get_client(self, name: str) -> Optional[MCPClient]:
        """
        Get an MCP client by name

        Args:
            name: Server name

        Returns:
            MCP client or None
        """
        return self.clients.get(name)

    def list_servers(self) -> List[str]:
        """Get list of connected server names"""
        return list(self.clients.keys())

    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all tools from all servers

        Returns:
            Dict mapping server name to list of tools
        """
        all_tools = {}
        for name, client in self.clients.items():
            try:
                tools = client.list_tools()
                all_tools[name] = tools
            except Exception as e:
                print(f"Error getting tools from {name}: {e}")
                all_tools[name] = []

        return all_tools

    def get_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all resources from all servers

        Returns:
            Dict mapping server name to list of resources
        """
        all_resources = {}
        for name, client in self.clients.items():
            try:
                resources = client.list_resources()
                all_resources[name] = resources
            except Exception as e:
                print(f"Error getting resources from {name}: {e}")
                all_resources[name] = []

        return all_resources

    def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all servers

        Returns:
            Dict mapping server name to health status
        """
        health_status = {}
        for name, client in self.clients.items():
            health_status[name] = client.health_check()

        return health_status

    def get_server_info_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get info from all servers

        Returns:
            Dict mapping server name to server info
        """
        all_info = {}
        for name, client in self.clients.items():
            all_info[name] = client.get_server_info()

        return all_info
