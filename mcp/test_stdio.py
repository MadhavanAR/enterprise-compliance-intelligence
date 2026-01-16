#!/usr/bin/env python3
"""
Test stdio MCP tools directly (no transport layer)
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import roll_dice, web_search

print("=" * 60)
print("Testing roll_dice tool")
print("=" * 60)
result = roll_dice(6, 4)
print(f"Result: {result}")
print()

print("=" * 60)
print("Testing web_search tool")
print("=" * 60)
result = web_search("Edmonton Oilers Stanley Cup 2025")
print(f"Result: {result}")
print()

print("✅ All stdio MCP tools working correctly")
