"""Mistral AI Provider Implementation"""

from typing import List, Iterator
from mistralai import Mistral
from .base import BaseProvider, Message, ChatResponse, StreamChunk


class MistralProvider(BaseProvider):
    """Mistral AI API provider"""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = Mistral(api_key=api_key)

    def get_available_models(self) -> List[str]:
        """Return list of available Mistral models"""
        return [
            "mistral-large-latest",
            "mistral-small-latest",
            "mistral-medium-latest",
            "codestral-latest",
            "mistral-embed",
        ]

    def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> ChatResponse:
        """Send a chat completion request to Mistral"""
        # Convert messages to Mistral format
        mistral_messages = [msg.to_dict() for msg in messages]

        # Make API call
        response = self.client.chat.complete(
            model=model,
            messages=mistral_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Extract response
        choice = response.choices[0]
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        } if hasattr(response, 'usage') and response.usage else None

        return ChatResponse(
            content=choice.message.content,
            model=response.model,
            finish_reason=choice.finish_reason,
            usage=usage
        )

    def stream_chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Iterator[StreamChunk]:
        """Stream a chat completion from Mistral"""
        # Convert messages to Mistral format
        mistral_messages = [msg.to_dict() for msg in messages]

        # Make streaming API call
        stream = self.client.chat.stream(
            model=model,
            messages=mistral_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Yield chunks
        for chunk in stream:
            if chunk.data.choices:
                choice = chunk.data.choices[0]
                if choice.delta.content:
                    yield StreamChunk(
                        content=choice.delta.content,
                        finish_reason=choice.finish_reason
                    )

    def supports_function_calling(self) -> bool:
        """Mistral supports function calling"""
        return True
