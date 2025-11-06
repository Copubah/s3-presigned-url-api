"""
Rate limiting and throttling for S3 Presigned URL API
"""

from fastapi import HTTPException, Request, status
from typing import Dict, Optional
import time
import asyncio
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter implementation"""
    
    def __init__(self):
        # Rate limits per endpoint per user (requests per minute)
        self.rate_limits = {
            "upload": 10,    # 10 upload URLs per minute
            "download": 30,  # 30 download URLs per minute
            "list": 5,       # 5 list requests per minute
            "delete": 5      # 5 delete requests per minute
        }
        
        # Storage for rate limit tracking
        self.user_requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.cleanup_interval = 300  # Clean up old entries every 5 minutes
        self.last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove old request entries to prevent memory leaks"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
            
        cutoff_time = current_time - 60  # Keep only last minute
        
        for user_id in list(self.user_requests.keys()):
            for endpoint in list(self.user_requests[user_id].keys()):
                requests = self.user_requests[user_id][endpoint]
                
                # Remove old requests
                while requests and requests[0] < cutoff_time:
                    requests.popleft()
                
                # Clean up empty structures
                if not requests:
                    del self.user_requests[user_id][endpoint]
            
            if not self.user_requests[user_id]:
                del self.user_requests[user_id]
        
        self.last_cleanup = current_time
    
    def is_allowed(self, user_id: str, endpoint: str) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed under rate limits
        Returns (is_allowed, retry_after_seconds)
        """
        self._cleanup_old_entries()
        
        current_time = time.time()
        limit = self.rate_limits.get(endpoint, 60)  # Default 60 per minute
        
        # Get user's requests for this endpoint
        user_endpoint_requests = self.user_requests[user_id][endpoint]
        
        # Remove requests older than 1 minute
        while user_endpoint_requests and user_endpoint_requests[0] < current_time - 60:
            user_endpoint_requests.popleft()
        
        # Check if under limit
        if len(user_endpoint_requests) < limit:
            user_endpoint_requests.append(current_time)
            logger.debug(f"Rate limit check passed for user {user_id}, endpoint {endpoint}")
            return True, None
        
        # Calculate retry after time
        oldest_request = user_endpoint_requests[0]
        retry_after = int(60 - (current_time - oldest_request)) + 1
        
        logger.warning(f"Rate limit exceeded for user {user_id}, endpoint {endpoint}")
        return False, retry_after

# Global rate limiter instance
rate_limiter = RateLimiter()

async def check_rate_limit(request: Request, user_id: str, endpoint: str):
    """Dependency to check rate limits"""
    is_allowed, retry_after = rate_limiter.is_allowed(user_id, endpoint)
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for user {user_id} on {endpoint}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for {endpoint}. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
    
    return True