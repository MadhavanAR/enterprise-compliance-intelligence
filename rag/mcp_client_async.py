"""
Async MCP client with caching and circuit breaker
"""
import asyncio
import sys
import os
from typing import Dict, Any, Optional
from rag.logger import get_logger
from rag.cache import tool_cache

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp'))
from mcp.server import roll_dice, web_search

# Circuit breaker state
_circuit_breaker_state: Dict[str, dict] = {
    "roll_dice": {"failures": 0, "last_failure": None, "open": False},
    "web_search": {"failures": 0, "last_failure": None, "open": False}
}

CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60  # seconds

async def call_tool_async(name: str, args: Dict[str, Any], trace_id: str = None) -> Dict[str, Any]:
    """
    Call an MCP tool asynchronously with caching and circuit breaker.
    
    Features:
    - Tool result caching (web_search especially)
    - Circuit breaker (prevents cascade failures)
    - Async execution (non-blocking)
    """
    logger = get_logger(trace_id)
    
    # Check circuit breaker
    if _is_circuit_open(name):
        logger.warning("Circuit breaker open", tool=name)
        raise RuntimeError(f"Circuit breaker open for {name} (too many failures)")
    
    # Check cache (especially useful for web_search)
    cached_result = tool_cache.get(name, args)
    if cached_result:
        logger.info("Tool cache hit", tool=name)
        return cached_result
    
    logger.start_timer(f"tool_{name}")
    
    try:
        # Run tool in executor (non-blocking)
        if name == "roll_dice":
            sides = args.get("sides", 6)
            count = args.get("count", 1)
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, roll_dice, sides, count)
        
        elif name == "web_search":
            query = args.get("query", "")
            if not query:
                raise ValueError("web_search requires 'query' argument")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, web_search, query)
        
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Cache result (especially for web_search)
        tool_cache.set(name, args, result)
        
        # Reset circuit breaker on success
        _reset_circuit(name)
        
        logger.end_timer(f"tool_{name}", tool=name)
        logger.info("Tool call successful", tool=name)
        
        return result
    
    except Exception as e:
        # Track failure
        _record_failure(name)
        logger.error("Tool call failed", tool=name, error=str(e))
        raise

def _is_circuit_open(tool_name: str) -> bool:
    """Check if circuit breaker is open."""
    import time
    
    state = _circuit_breaker_state.get(tool_name, {})
    
    if not state.get("open", False):
        return False
    
    # Check if timeout has passed
    last_failure = state.get("last_failure", 0)
    if time.time() - last_failure > CIRCUIT_BREAKER_TIMEOUT:
        _reset_circuit(tool_name)
        return False
    
    return True

def _record_failure(tool_name: str):
    """Record a failure and potentially open circuit breaker."""
    import time
    
    state = _circuit_breaker_state.setdefault(tool_name, {"failures": 0, "last_failure": None, "open": False})
    state["failures"] += 1
    state["last_failure"] = time.time()
    
    if state["failures"] >= CIRCUIT_BREAKER_THRESHOLD:
        state["open"] = True

def _reset_circuit(tool_name: str):
    """Reset circuit breaker on success."""
    state = _circuit_breaker_state.get(tool_name, {})
    state["failures"] = 0
    state["open"] = False
    state["last_failure"] = None

# Sync wrapper for backward compatibility
def call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Sync wrapper for async tool calls."""
    return asyncio.run(call_tool_async(name, args))
