import json
import redis.asyncio as redis
from typing import Any, Optional, Dict, List
from ..config import settings


class RedisCache:
    """Redis-based caching and state management."""

    def __init__(self):
        self.redis = None

    async def connect(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(
            settings.redis.url,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    async def set(self, key: str, value: Any, ttl: int = None):
        """Set a cache value."""
        serialized_value = json.dumps(value) if not isinstance(value, str) else value
        if ttl:
            await self.redis.setex(key, ttl, serialized_value)
        else:
            await self.redis.set(key, serialized_value)

    async def get(self, key: str) -> Optional[Any]:
        """Get a cache value."""
        value = await self.redis.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def delete(self, key: str):
        """Delete a cache key."""
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return await self.redis.exists(key)

    # Agent state management
    async def save_agent_state(self, query_id: str, agent_name: str, state: Dict[str, Any]):
        """Save agent execution state."""
        key = f"agent_state:{query_id}:{agent_name}"
        await self.set(key, state, ttl=86400)  # 24 hours

    async def get_agent_state(self, query_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent execution state."""
        key = f"agent_state:{query_id}:{agent_name}"
        return await self.get(key)

    async def save_concept_vector(self, query_id: str, concept_vector: Dict[str, float], ttl: int = 3600):
        """Cache concept vectors for faster re-processing."""
        key = f"concept_vector:{query_id}"
        await self.set(key, concept_vector, ttl=ttl)

    async def get_concept_vector(self, query_id: str) -> Optional[Dict[str, float]]:
        """Retrieve cached concept vector."""
        key = f"concept_vector:{query_id}"
        return await self.get(key)

    async def cache_api_response(self, tool_name: str, params_hash: str, response: Any, ttl: int = 1800):
        """Cache API responses to reduce redundant calls."""
        key = f"api_cache:{tool_name}:{params_hash}"
        await self.set(key, response, ttl=ttl)

    async def get_cached_api_response(self, tool_name: str, params_hash: str) -> Optional[Any]:
        """Retrieve cached API response."""
        key = f"api_cache:{tool_name}:{params_hash}"
        return await self.get(key)

    # Rate limiting
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded."""
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window)
        return current <= limit

    async def get_rate_limit_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests in current window."""
        current = await self.redis.get(key)
        current = int(current) if current else 0
        return max(0, limit - current)

    # Metrics and analytics
    async def increment_counter(self, key: str, amount: int = 1):
        """Increment a counter (e.g., API calls, agent executions)."""
        await self.redis.incrby(key, amount)

    async def get_counter(self, key: str) -> int:
        """Get counter value."""
        value = await self.redis.get(key)
        return int(value) if value else 0

    async def add_to_set(self, key: str, member: str):
        """Add member to a set."""
        await self.redis.sadd(key, member)

    async def get_set_members(self, key: str) -> List[str]:
        """Get all members of a set."""
        return await self.redis.smembers(key)

    async def publish_event(self, channel: str, message: Dict[str, Any]):
        """Publish event to Redis pub/sub."""
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe_to_events(self, channel: str):
        """Subscribe to Redis pub/sub events."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


# Global cache instance
cache = RedisCache()


async def get_cache():
    """Dependency for FastAPI to get cache instance."""
    if not cache.redis:
        await cache.connect()
    try:
        yield cache
    finally:
        pass  # Keep connection open for app lifetime
