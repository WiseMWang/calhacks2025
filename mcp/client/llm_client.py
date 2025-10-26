import openai
import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp import types
import json
import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found")
        self.client = openai.OpenAI(api_key=self.api_key)
        self.session = None
    
    async def connect_to_server(self, server_command):
        """Connect to MCP server using proper session"""
        server_params = StdioServerParameters(command=server_command)
        self.stdio_context = stdio_client(server_params)
        
        # Add timeout to prevent hanging
        try:
            with anyio.fail_after(10):  # 10 second timeout
                read_stream, write_stream = await self.stdio_context.__aenter__()
                self.session = ClientSession(read_stream, write_stream)
                await self.session.initialize()
        except TimeoutError:
            logger.error("Timeout connecting to MCP server")
            raise RuntimeError("MCP server connection timeout")
    
    async def get_tools(self):
        """Get tools from MCP server"""
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        result = await self.session.list_tools()
        return result.tools
    
    async def call_tool(self, name, arguments):
        """Call a tool via MCP"""
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        return await self.session.call_tool(name, arguments)
    
    async def query(self, user_input, server_command="python", server_args=["../../server/mcp_server.py"]):
        """Query GPT-4o-mini with MCP tools"""
        try:
            # Add timeout for entire operation
            with anyio.fail_after(30):  # 30 second total timeout
                await self.connect_to_server(server_command)
                
                # Get available tools
                tools = await self.get_tools()
                
                # Convert to OpenAI format
                openai_tools = [{
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema
                    }
                } for tool in tools]
                
                # Initial GPT call with system message
                messages = [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant that can send emails via Gmail. When the user asks to send an email, use the send_email tool."
                    },
                    {
                        "role": "user", 
                        "content": user_input
                    }
                ]
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=openai_tools
                )
                
                message = response.choices[0].message
                
                # Handle tool calls
                if message.tool_calls:
                    messages.append(message)
                    
                    for tool_call in message.tool_calls:
                        # Execute tool via MCP
                        tool_result = await self.call_tool(
                            tool_call.function.name,
                            json.loads(tool_call.function.arguments)
                        )
                        
                        # Add tool result to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(tool_result.content[0].text if tool_result.content else "Success")
                        })
                    
                    # Get final response
                    final_response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages
                    )
                    return final_response.choices[0].message.content
                
                return message.content
                
        except TimeoutError:
            logger.error("Query timeout - MCP server may be unresponsive")
            raise RuntimeError("Query timeout")
        finally:
            if hasattr(self, 'stdio_context') and self.stdio_context:
                try:
                    await self.stdio_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning(f"Error closing MCP connection: {e}")

async def run_llm_query(query, api_key, server_command="python", server_args=["../../server/mcp_server.py"]):
    """Run LLM query with MCP integration"""
    client = LLMClient(api_key)
    return await client.query(query, server_command, server_args)