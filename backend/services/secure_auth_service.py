"""
Secure Authentication Service
Handles magic link generation, token hashing, and session management with security best practices.
"""

import hashlib
import secrets
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

# Security pepper from environment (fallback for local dev)
AUTH_PEPPER = os.environ.get('AUTH_TOKEN_PEPPER', 'dev-pepper-change-in-prod')

class SecureAuthService:
    """Service for secure authentication operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def generate_magic_token(self) -> str:
        """
        Generate a cryptographically secure magic link token.
        Returns the raw token (to be sent in email), NOT the hash.
        """
        # Generate 32 bytes of random data = 64 hex characters
        return secrets.token_urlsafe(32)
    
    def hash_token(self, token: str) -> str:
        """
        Hash a token with SHA256 + pepper for secure storage.
        
        Args:
            token: Raw token string
            
        Returns:
            SHA256 hash hex string
        """
        # Combine token with pepper for additional security
        combined = f"{token}{AUTH_PEPPER}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    async def create_magic_link(
        self, 
        email: str, 
        action: str = "login",
        metadata: Optional[dict] = None
    ) -> Tuple[str, str]:
        """
        Create a magic link token and store its hash in database.
        
        Args:
            email: User email
            action: Action type ('login', 'pre_checkout', etc.)
            metadata: Additional data (package_id, etc.)
            
        Returns:
            Tuple of (raw_token, token_hash)
        """
        # Generate secure token
        raw_token = self.generate_magic_token()
        token_hash = self.hash_token(raw_token)
        
        # Store hashed token in database
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        token_doc = {
            "token_hash": token_hash,
            "email": email,
            "action": action,
            "metadata": metadata or {},
            "expires_at": expires_at,
            "used": False,
            "created_at": datetime.now(timezone.utc),
            "ip_address": None,  # Set by endpoint if needed
        }
        
        await self.db.magic_tokens.insert_one(token_doc)
        
        logger.info(
            f"Magic link created for {email} (action: {action})",
            extra={"email": email, "action": action}
        )
        
        return raw_token, token_hash
    
    async def verify_magic_token(
        self, 
        raw_token: str,
        expected_action: Optional[str] = None
    ) -> Optional[dict]:
        """
        Verify a magic token and return associated data if valid.
        
        Args:
            raw_token: Token received from user
            expected_action: Expected action type (optional check)
            
        Returns:
            Token document if valid, None otherwise
        """
        # Hash the provided token
        token_hash = self.hash_token(raw_token)
        
        # Find token in database
        token_doc = await self.db.magic_tokens.find_one({
            "token_hash": token_hash,
            "used": False
        })
        
        if not token_doc:
            # Check if token was already used (for better error message)
            used_token = await self.db.magic_tokens.find_one({"token_hash": token_hash})
            if used_token:
                logger.warning(f"Attempt to reuse magic token for {used_token.get('email')}")
                return None
            else:
                logger.warning("Invalid magic token attempted")
                return None
        
        # Check expiration
        expires_at = token_doc.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
        elif isinstance(expires_at, datetime) and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        
        if expires_at < now:
            logger.warning(f"Expired magic token for {token_doc.get('email')}")
            # Clean up expired token
            await self.db.magic_tokens.delete_one({"_id": token_doc["_id"]})
            return None
        
        # Check action if specified
        if expected_action and token_doc.get('action') != expected_action:
            logger.warning(
                f"Action mismatch for token: expected {expected_action}, got {token_doc.get('action')}"
            )
            return None
        
        return token_doc
    
    async def mark_token_used(self, token_hash: str) -> bool:
        """Mark a token as used to prevent replay attacks."""
        result = await self.db.magic_tokens.update_one(
            {"token_hash": token_hash},
            {"$set": {"used": True, "used_at": datetime.now(timezone.utc)}}
        )
        return result.modified_count > 0
    
    async def log_auth_attempt(
        self,
        email: str,
        action: str,
        success: bool,
        ip_address: Optional[str] = None,
        error_msg: Optional[str] = None
    ):
        """Log authentication attempts for security auditing."""
        log_entry = {
            "email": email,
            "action": action,
            "success": success,
            "ip_address": ip_address,
            "error_msg": error_msg,
            "timestamp": datetime.now(timezone.utc)
        }
        
        await self.db.auth_logs.insert_one(log_entry)
        
        if not success:
            logger.warning(
                f"Auth attempt failed: {action} for {email}",
                extra=log_entry
            )







