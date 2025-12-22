"""
Stub implementation of StripeCheckout for local development.
This allows the application to start without the actual emergentintegrations package.
"""
from typing import Optional, Dict, Any


class CheckoutSessionRequest:
    """Stub CheckoutSessionRequest class"""
    pass


class CheckoutSessionResponse:
    """Stub CheckoutSessionResponse class"""
    def __init__(self, url: str = ""):
        self.url = url


class CheckoutStatusResponse:
    """Stub CheckoutStatusResponse class"""
    def __init__(self, status: str = "pending"):
        self.status = status


class StripeCheckout:
    """Stub StripeCheckout class for local development"""
    
    def __init__(self, api_key: Optional[str] = None, webhook_url: Optional[str] = None):
        self.api_key = api_key
        self.webhook_url = webhook_url
    
    async def create_checkout_session(self, request: CheckoutSessionRequest) -> CheckoutSessionResponse:
        """Stub method - returns empty response"""
        return CheckoutSessionResponse(url="")
    
    async def get_checkout_status(self, session_id: str) -> CheckoutStatusResponse:
        """Stub method - returns pending status"""
        return CheckoutStatusResponse(status="pending")
    
    async def handle_webhook(self, body: bytes, signature: str) -> Dict[str, Any]:
        """Stub method - returns empty dict"""
        return {}

