#!/usr/bin/env python3
"""
MCP Server - Implements Model Context Protocol from scratch
Handles JSON-RPC 2.0 requests over stdio
"""

import json
import sys
import logging
from typing import Dict, Any, Callable
from tools.gmail_tools import send_email, GmailTools
#from tools.drive_tools import DriveTools
from mcp.types import LATEST_PROTOCOL_VERSION, DEFAULT_NEGOTIATED_VERSION

# Set up logging to stderr (stdout is used for JSON-RPC communication)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server implementing JSON-RPC 2.0 protocol"""

    def __init__(self):
        """Initialize MCP server with available tools"""
        # Initialize tool modules
        self.gmail_tools = GmailTools()
       # self.drive_tools = DriveTools()

        # Register available tools
        self.tools = {
            "send_email": {
                "function": self.gmail_tools.send_email,
                "schema": {
                    "name": "send_email",
                    "description": "Send an email via Gmail to specified recipients",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Recipient email address"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Email subject line"
                            },
                            "body": {
                                "type": "string",
                                "description": "Email body content (plain text or HTML)"
                            },
                            "cc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "CC recipients (optional)"
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            }#,
            # "search_drive_files": {
            #     "function": self.drive_tools.search_files,
            #     "schema": {
            #         "name": "search_drive_files",
            #         "description": "Search for files in Google Drive by name or query",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "query": {
            #                     "type": "string",
            #                     "description": "Search query (file name or keywords)"
            #                 },
            #                 "max_results": {
            #                     "type": "integer",
            #                     "description": "Maximum number of results to return (default: 10)"
            #                 }
            #             },
            #             "required": ["query"]
            #         }
            #     }
            # }
        }

        logger.info(f"MCP Server initialized with {len(self.tools)} tools")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming JSON-RPC 2.0 request

        Args:
            request: JSON-RPC request object

        Returns:
            Result dictionary to be sent back to client
        """
        method = request.get("method")
        params = request.get("params", {})

        logger.info(f"Handling request: {method}")

        if method == "tools/list":
            # Return list of available tools
            return {
                "tools": [tool["schema"] for tool in self.tools.values()]
            }

        elif method == "tools/call":
            # Execute a specific tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.tools:
                raise ValueError(f"Unknown tool: {tool_name}")

            logger.info(f"Calling tool: {tool_name} with args: {arguments}")

            # Execute the tool function
            result = self.tools[tool_name]["function"](**arguments)

            # Return in MCP format
            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }

        elif method == "initialize":
            # Handle initialization request
            return {
                "protocolVersion": LATEST_PROTOCOL_VERSION,
                "serverInfo": {
                    "name": "google-workspace-mcp-server",
                    "version": "0.1.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        
        elif method == "notifications/initialized":
        # Client confirms initialization complete
            logger.info("Client initialized successfully")
            return "notification" # Notifications don't get responses

        else:
            raise ValueError(f"Unknown method: {method}")

    def run(self):
        """
        Main server loop - reads JSON-RPC requests from stdin,
        processes them, and writes responses to stdout
        """
        logger.info("MCP Server starting...")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON-RPC request
                    request = json.loads(line)
                    request_id = request.get("id")

                    # Process request
                    result = self.handle_request(request)

                    # Build JSON-RPC response
                    if request_id is not None:
                        # Ensure result is a dict
                        if result is None:
                            result = {}
                        elif not isinstance(result, dict):
                            result = {"content": result}  # wrap non-dict results

                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id if request_id is not None else 0,
                            "result": result
                        }
                        if request_id is not None and result != "notification":
                            print(json.dumps(response), flush=True)

                except Exception as e:
                    logger.error(f"Error handling request: {e}", exc_info=True)
                    # Build JSON-RPC error response
                    if 'request' in locals() and request.get("id") is not None:
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "error": {
                                "code": -32603,
                                "message": str(e)
                            }
                        }
                        print(json.dumps(error_response), flush=True)

                # Send response to stdout (client reads from here)
                print(json.dumps(response), flush=True)

        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    server = MCPServer()
    server.run()
