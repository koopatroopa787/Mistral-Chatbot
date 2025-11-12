"""Anthropic Claude Provider Implementation"""

from typing import List, Iterator
from anthropic import Anthropic
from .base import BaseProvider, Message, ChatResponse, StreamChunk, MessageRole


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider"""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = Anthropic(api_key=api_key)

    def get_available_models(self) -> List[str]:
        """Return list of available Anthropic models"""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def _prepare_messages(self, messages: List[Message]) -> tuple:
        """Prepare messages for Anthropic API (system message separate)"""
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

        return system_message, anthropic_messages

    def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> ChatResponse:
        """Send a chat completion request to Anthropic"""
        system_message, anthropic_messages = self._prepare_messages(messages)

        # Build request parameters
        request_params = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        if system_message:
            request_params["system"] = system_message

        # Make API call
        response = self.client.messages.create(**request_params)

        # Extract response
        content = response.content[0].text if response.content else ""
        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }

        return ChatResponse(
            content=content,
            model=response.model,
            finish_reason=response.stop_reason,
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
        """Stream a chat completion from Anthropic"""
        system_message, anthropic_messages = self._prepare_messages(messages)

        # Build request parameters
        request_params = {
            "model": model,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }

        if system_message:
            request_params["system"] = system_message

        # Make streaming API call
        with self.client.messages.stream(**request_params) as stream:
            for text in stream.text_stream:
                yield StreamChunk(content=text)

    def supports_function_calling(self) -> bool:
        """Anthropic supports tool use"""
        return True
