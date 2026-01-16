"""
MCP Client - stdio mode (Cursor-compatible)
- Direct Python function calls (no HTTP)
- Zero business logic - just tool calling
- Agent-safe
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp'))

from mcp.server import roll_dice, web_search

def call_tool(name: str, args: dict) -> dict:
    """
    Call an MCP tool by name with arguments (stdio mode).
    
    Args:
        name: Tool name ('roll_dice' or 'web_search')
        args: Tool arguments as dict
    
    Returns:
        Tool result as dict
    """
    if name == "roll_dice":
        sides = args.get("sides", 6)
        count = args.get("count", 1)
        return roll_dice(sides, count)
    
    elif name == "web_search":
        query = args.get("query", "")
        if not query:
            raise ValueError("web_search requires 'query' argument")
        return web_search(query)
    
    else:
        raise ValueError(f"Unknown tool: {name}")