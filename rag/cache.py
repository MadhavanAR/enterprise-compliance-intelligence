"""
Caching layer for performance optimization
- Query → retrieved docs cache (LRU)
- Embeddings cache (hash(text) → vector)
- Tool results cache
"""
import hashlib
import json
from functools import lru_cache
from typing import Optional, Dict, Any, List
from rag.config import get_config
from rag.logger import get_logger

logger = get_logger()

# In-memory caches (can be replaced with Redis for distributed systems)
_query_cache: Dict[str, List[str]] = {}
_embedding_cache: Dict[str, List[float]] = {}
_tool_cache: Dict[str, Any] = {}

def _hash_query(query: str) -> str:
    """Create hash key for query caching."""
    return hashlib.md5(query.lower().strip().encode()).hexdigest()

def _hash_text(text: str) -> str:
    """Create hash key for embedding caching."""
    return hashlib.md5(text.encode()).hexdigest()

class QueryCache:
    """LRU cache for query → retrieved docs."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, List[str]] = {}
        self.access_order: List[str] = []
    
    def get(self, query: str) -> Optional[List[str]]:
        """Get cached results for query."""
        key = _hash_query(query)
        if key in self.cache:
            # Move to end (most recently used)
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            logger.debug("Query cache hit", query_preview=query[:50])
            return self.cache[key]
        logger.debug("Query cache miss", query_preview=query[:50])
        return None
    
    def set(self, query: str, docs: List[str]):
        """Cache query results."""
        key = _hash_query(query)
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        self.cache[key] = docs
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.access_order.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": "N/A"  # Would need hit/miss tracking
        }

class EmbeddingCache:
    """Cache for text → embedding vectors."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, List[float]] = {}
    
    def get(self, text: str) -> Optional[List[float]]:
        """Get cached embedding."""
        key = _hash_text(text)
        if key in self.cache:
            logger.debug("Embedding cache hit", text_length=len(text))
            return self.cache[key]
        logger.debug("Embedding cache miss", text_length=len(text))
        return None
    
    def set(self, text: str, embedding: List[float]):
        """Cache embedding."""
        key = _hash_text(text)
        
        # Simple eviction (could use LRU)
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remove random entry (simple eviction)
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        self.cache[key] = embedding
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()

class ToolCache:
    """Cache for tool results (web_search, etc.)."""
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple[Any, float]] = {}  # (result, timestamp)
    
    def get(self, tool_name: str, args: Dict[str, Any]) -> Optional[Any]:
        """Get cached tool result."""
        import time
        key = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
        
        if key in self.cache:
            result, timestamp = self.cache[key]
            age = time.time() - timestamp
            
            if age < self.ttl_seconds:
                logger.debug("Tool cache hit", tool=tool_name, age_seconds=round(age, 2))
                return result
            else:
                # Expired
                del self.cache[key]
        
        logger.debug("Tool cache miss", tool=tool_name)
        return None
    
    def set(self, tool_name: str, args: Dict[str, Any], result: Any):
        """Cache tool result."""
        import time
        key = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
        
        # Evict if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        self.cache[key] = (result, time.time())

# Global cache instances
query_cache = QueryCache(max_size=1000)
embedding_cache = EmbeddingCache(max_size=10000)
tool_cache = ToolCache(max_size=500, ttl_seconds=3600)
