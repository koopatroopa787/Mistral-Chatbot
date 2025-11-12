"""OpenAI Provider Implementation"""

from typing import List, Iterator
from openai import OpenAI
from .base import BaseProvider, Message, ChatResponse, StreamChunk


class OpenAIProvider(BaseProvider):
    """OpenAI API provider"""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = OpenAI(api_key=api_key)

    def get_available_models(self) -> List[str]:
        """Return list of available OpenAI models"""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "o1-preview",
            "o1-mini",
        ]

    def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> ChatResponse:
        """Send a chat completion request to OpenAI"""
        # Convert messages to OpenAI format
        openai_messages = [msg.to_dict() for msg in messages]

        # Make API call
        response = self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
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
        } if response.usage else None

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
        """Stream a chat completion from OpenAI"""
        # Convert messages to OpenAI format
        openai_messages = [msg.to_dict() for msg in messages]

        # Make streaming API call
        stream = self.client.chat.completions.create(
            model=model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )

        # Yield chunks
        for chunk in stream:
            if chunk.choices:
                choice = chunk.choices[0]
                if choice.delta.content:
                    yield StreamChunk(
                        content=choice.delta.content,
                        finish_reason=choice.finish_reason
                    )

    def supports_function_calling(self) -> bool:
        """OpenAI supports function calling"""
        return True
