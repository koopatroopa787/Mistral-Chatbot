"""Application Settings"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path
import json
import os


@dataclass
class ProviderSettings:
    """Settings for an AI provider"""
    name: str
    api_key: str
    default_model: str
    enabled: bool = True


@dataclass
class Settings:
    """Application settings"""

    # General settings
    app_name: str = "Universal AI Chatbot"
    version: str = "2.0.0"

    # Default provider
    default_provider: str = "mistral"

    # Provider configurations
    providers: Dict[str, ProviderSettings] = None

    # Model parameters
    default_temperature: float = 0.7
    default_max_tokens: int = 1000
    max_history_length: int = 10

    # UI settings
    theme: str = "dark"
    show_token_usage: bool = True
    enable_streaming: bool = True

    # Document indexing
    index_type: str = "simple"
    embedding_model: str = "mistral-embed"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # MCP settings
    enable_mcp: bool = True
    mcp_config_path: str = "config/mcp_servers.json"

    # Advanced features
    enable_conversation_export: bool = True
    enable_response_grading: bool = True
    enable_conversation_flows: bool = True

    # System prompts
    default_system_prompt: str = "You are a helpful AI assistant that provides accurate and concise information."

    def __post_init__(self):
        """Initialize providers dict if not set"""
        if self.providers is None:
            self.providers = {}

    def add_provider(self, name: str, api_key: str, default_model: str, enabled: bool = True):
        """Add or update a provider"""
        self.providers[name] = ProviderSettings(
            name=name,
            api_key=api_key,
            default_model=default_model,
            enabled=enabled
        )

    def get_provider_api_key(self, provider_name: str) -> Optional[str]:
        """Get API key for a provider"""
        # First check environment variables
        env_key = f"{provider_name.upper()}_API_KEY"
        env_value = os.getenv(env_key)
        if env_value:
            return env_value

        # Then check settings
        if provider_name in self.providers:
            return self.providers[provider_name].api_key

        return None

    def get_enabled_providers(self) -> list:
        """Get list of enabled provider names"""
        return [
            name for name, config in self.providers.items()
            if config.enabled and config.api_key
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        result = asdict(self)
        # Convert provider settings to dicts
        if self.providers:
            result['providers'] = {
                name: asdict(config) for name, config in self.providers.items()
            }
        return result


def load_settings(config_path: Path = None) -> Settings:
    """
    Load settings from file

    Args:
        config_path: Path to config file (default: config/settings.json)

    Returns:
        Settings object
    """
    if config_path is None:
        config_path = Path("config/settings.json")

    if not config_path.exists():
        # Create default settings
        settings = Settings()
        save_settings(settings, config_path)
        return settings

    try:
        with open(config_path, 'r') as f:
            data = json.load(f)

        # Convert providers dict to ProviderSettings objects
        if 'providers' in data and data['providers']:
            data['providers'] = {
                name: ProviderSettings(**config)
                for name, config in data['providers'].items()
            }

        return Settings(**data)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return Settings()


def save_settings(settings: Settings, config_path: Path = None):
    """
    Save settings to file

    Args:
        settings: Settings object
        config_path: Path to config file (default: config/settings.json)
    """
    if config_path is None:
        config_path = Path("config/settings.json")

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, 'w') as f:
            json.dump(settings.to_dict(), f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")
