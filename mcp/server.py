#!/usr/bin/env python3
"""
MCP Server with roll_dice and web_search tools
"""
import random
import requests
import json
import sys
from typing import Any

def roll_dice(sides: int = 6, count: int = 1) -> dict:
    """Roll dice and return results."""
    results = [random.randint(1, sides) for _ in range(count)]
    total = sum(results)
    return {
        "results": results,
        "total": total,
        "sides": sides,
        "count": count
    }

def web_search(query: str) -> dict:
    """
    Perform web search and return structured results.
    
    Improved output quality:
    - Extracts structured answer if available
    - Marks explicitly as "no verified answer" if not available
    """
    # Using DuckDuckGo instant answer API (no API key needed)
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        abstract = data.get("AbstractText", "")
        answer = data.get("Answer", "")
        answer_type = data.get("AnswerType", "")
        
        # Improved parsing: prefer structured answer, fallback to abstract
        if answer and answer.strip():
            result_text = answer
            has_verified_answer = True
        elif abstract and abstract.strip():
            result_text = abstract
            has_verified_answer = True
        else:
            # Explicit mark for no verified answer (not vague phrase)
            result_text = f"No verified answer available for: {query}"
            has_verified_answer = False
        
        return {
            "query": query,
            "result": result_text,
            "answer_type": answer_type,
            "source": "DuckDuckGo",
            "has_verified_answer": has_verified_answer  # Explicit flag
        }
    except Exception as e:
        return {
            "query": query,
            "result": f"Search failed: {str(e)}",
            "error": True,
            "has_verified_answer": False
        }

def handle_request(request: dict) -> dict:
    """Handle MCP tool call request."""
    method = request.get("method")
    params = request.get("params", {})
    
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "roll_dice":
            sides = arguments.get("sides", 6)
            count = arguments.get("count", 1)
            result = roll_dice(sides, count)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        
        elif tool_name == "web_search":
            query = arguments.get("query", "")
            result = web_search(query)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "roll_dice",
                        "description": "Roll dice with specified sides and count",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "sides": {
                                    "type": "integer",
                                    "description": "Number of sides on each die",
                                    "default": 6
                                },
                                "count": {
                                    "type": "integer",
                                    "description": "Number of dice to roll",
                                    "default": 1
                                }
                            },
                            "required": []
                        }
                    },
                    {
                        "name": "web_search",
                        "description": "Search the web for current information",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }
    
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "error": {
            "code": -32601,
            "message": f"Unknown method: {method}"
        }
    }

if __name__ == "__main__":
    print("MCP Server starting...", file=sys.stderr)
    print("Available tools: roll_dice, web_search", file=sys.stderr)
    print("Server ready. Listening for requests...", file=sys.stderr)
    
    # Simple stdin/stdout JSON-RPC server
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
