"""Base provider interface for AI models"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Iterator, AsyncIterator
from enum import Enum


class MessageRole(Enum):
    """Message roles in a conversation"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """Represents a single message in a conversation"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format"""
        result = {
            "role": self.role.value,
            "content": self.content
        }
        if self.name:
            result["name"] = self.name
        return result


@dataclass
class StreamChunk:
    """Represents a chunk of streamed response"""
    content: str
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    """Represents a complete chat response"""
    content: str
    model: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """Base class for all AI providers"""

    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the provider

        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific arguments
        """
        self.api_key = api_key
        self.kwargs = kwargs

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Return list of available models for this provider"""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> ChatResponse:
        """
        Send a chat completion request

        Args:
            messages: List of conversation messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse object
        """
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Iterator[StreamChunk]:
        """
        Send a streaming chat completion request

        Args:
            messages: List of conversation messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters

        Yields:
            StreamChunk objects
        """
        pass

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming"""
        return True

    def supports_function_calling(self) -> bool:
        """Check if provider supports function calling"""
        return False

    def get_provider_name(self) -> str:
        """Get the name of this provider"""
        return self.__class__.__name__.replace("Provider", "")

    def validate_model(self, model: str) -> bool:
        """Check if a model is valid for this provider"""
        return model in self.get_available_models()
