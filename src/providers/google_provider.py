"""Google Gemini Provider Implementation"""

from typing import List, Iterator
try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from .base import BaseProvider, Message, ChatResponse, StreamChunk, MessageRole


class GoogleProvider(BaseProvider):
    """Google Gemini API provider"""

    def __init__(self, api_key: str, **kwargs):
        if not GOOGLE_AVAILABLE:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")

        super().__init__(api_key, **kwargs)
        genai.configure(api_key=api_key)

    def get_available_models(self) -> List[str]:
        """Return list of available Google models"""
        return [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
        ]

    def _prepare_messages(self, messages: List[Message]) -> tuple:
        """Prepare messages for Google API"""
        system_instruction = None
        gemini_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "model"
                gemini_messages.append({
                    "role": role,
                    "parts": [msg.content]
                })

        return system_instruction, gemini_messages

    def chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> ChatResponse:
        """Send a chat completion request to Google"""
        system_instruction, gemini_messages = self._prepare_messages(messages)

        # Create model
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        model_kwargs = {"model_name": model}
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction

        gemini_model = genai.GenerativeModel(**model_kwargs)

        # Make API call
        response = gemini_model.generate_content(
            gemini_messages,
            generation_config=generation_config
        )

        # Extract response
        content = response.text if hasattr(response, 'text') else ""

        return ChatResponse(
            content=content,
            model=model,
            finish_reason=None,
            usage=None
        )

    def stream_chat(
        self,
        messages: List[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Iterator[StreamChunk]:
        """Stream a chat completion from Google"""
        system_instruction, gemini_messages = self._prepare_messages(messages)

        # Create model
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        model_kwargs = {"model_name": model}
        if system_instruction:
            model_kwargs["system_instruction"] = system_instruction

        gemini_model = genai.GenerativeModel(**model_kwargs)

        # Make streaming API call
        response = gemini_model.generate_content(
            gemini_messages,
            generation_config=generation_config,
            stream=True
        )

        # Yield chunks
        for chunk in response:
            if hasattr(chunk, 'text'):
                yield StreamChunk(content=chunk.text)

    def supports_function_calling(self) -> bool:
        """Google Gemini supports function calling"""
        return True
