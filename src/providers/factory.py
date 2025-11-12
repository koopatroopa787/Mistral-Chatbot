"""Provider Factory for creating AI provider instances"""

from typing import Dict, Type, Optional
from .base import BaseProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .mistral_provider import MistralProvider
from .google_provider import GoogleProvider


class ProviderFactory:
    """Factory for creating AI provider instances"""

    _providers: Dict[str, Type[BaseProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "mistral": MistralProvider,
        "google": GoogleProvider,
    }

    @classmethod
    def create(cls, provider_name: str, api_key: str, **kwargs) -> BaseProvider:
        """
        Create a provider instance

        Args:
            provider_name: Name of the provider (openai, anthropic, mistral, google)
            api_key: API key for the provider
            **kwargs: Additional provider-specific arguments

        Returns:
            Provider instance

        Raises:
            ValueError: If provider name is not supported
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"Unknown provider: {provider_name}. Available: {available}")

        provider_class = cls._providers[provider_name]
        return provider_class(api_key=api_key, **kwargs)

    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider names"""
        return list(cls._providers.keys())

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseProvider]):
        """
        Register a custom provider

        Args:
            name: Name for the provider
            provider_class: Provider class (must inherit from BaseProvider)
        """
        if not issubclass(provider_class, BaseProvider):
            raise ValueError("Provider class must inherit from BaseProvider")

        cls._providers[name.lower()] = provider_class
