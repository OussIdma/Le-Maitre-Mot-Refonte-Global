"""
Stub implementation of LlmChat and UserMessage for local development.
This allows the application to start without the actual emergentintegrations package.
"""
import asyncio
from typing import Optional


class UserMessage:
    """Stub UserMessage class"""
    def __init__(self, text: Optional[str] = None, content: Optional[str] = None):
        self.text = text or content or ""
        self.content = content or text or ""


class LlmChat:
    """Stub LlmChat class for local development"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        emergent_key: Optional[str] = None,
        session_id: Optional[str] = None,
        system_message: Optional[str] = None
    ):
        self.api_key = api_key or emergent_key
        self.session_id = session_id
        self.system_message = system_message
        self.model_provider = None
        self.model_name = None
    
    def with_model(self, provider: str, model: str):
        """Configure the model to use"""
        self.model_provider = provider
        self.model_name = model
        return self
    
    async def send_message(self, message: UserMessage, timeout: Optional[float] = None):
        """Stub method - returns empty response"""
        # Return a minimal response to prevent errors
        return '{"error": "emergentintegrations stub - LLM not available in local mode"}'
    
    async def run(self, message: UserMessage):
        """Stub method - returns empty response"""
        # Return a minimal response to prevent errors
        return "emergentintegrations stub - LLM not available in local mode"

