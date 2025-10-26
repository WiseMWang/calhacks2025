from flask import Flask, render_template, request, jsonify
import logging
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Add parent directory to path for MCP imports
sys.path.append(str(Path(__file__).parent.parent))
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
import mcp.types as types
import json

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from frontend"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        logger.info(f"Received message: {user_message}")
        
        # Use proper MCP client architecture
        response = asyncio.run(chat_with_mcp_tools(user_message))
        
        return jsonify({
            'success': True,
            'response': response
        })
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

async def get_mcp_tools():
    """Get available tools from MCP server using proper client session"""
    try:
        server_params = StdioServerParameters(command='python', args=['server/mcp_server.py'])
        
        async with stdio_client(server_params) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            await session.initialize()
            
            # Get tools using proper MCP protocol
            result = await session.list_tools()
            
            # Convert to OpenAI format
            tools = []
            for tool in result.tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or '',
                        "parameters": tool.inputSchema
                    }
                })
            
            return tools
        
    except Exception as e:
        logger.error(f"Error getting MCP tools: {e}")
        return []

async def call_mcp_tool(tool_name, arguments):
    """Call a tool via MCP server using proper client session"""
    try:
        server_params = StdioServerParameters(command='python', args=['server/mcp_server.py'])
        
        async with stdio_client(server_params) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            await session.initialize()
            
            # Call tool using proper MCP protocol
            result = await session.call_tool(tool_name, arguments)
            
            # Extract text from content
            if result.content and len(result.content) > 0:
                first_content = result.content[0]
                if hasattr(first_content, 'text'):
                    return first_content.text
            
            return "Tool executed successfully"
        
    except Exception as e:
        logger.error(f"Error calling MCP tool: {e}")
        return f"Error: {str(e)}"

async def chat_with_mcp_tools(user_message):
    """Chat with OpenAI using MCP tools"""
    try:
        # Get available tools
        tools = await get_mcp_tools()
        logger.info(f"Got {len(tools)} tools from MCP server")
        
        # Initial GPT call
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant that can send emails via Gmail. When the user asks to send an email, use the send_email tool."
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        response = openai_client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=messages,
            tools=tools if tools else None
        )
        
        message = response.choices[0].message
        
        # Check if GPT wants to call tools
        if message.tool_calls:
            logger.info(f"GPT wants to call {len(message.tool_calls)} tools")
            
            # Add assistant message to conversation
            messages.append(message)
            
            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                logger.info(f"Calling tool: {tool_name} with args: {arguments}")
                
                # Call the tool via MCP
                result = await call_mcp_tool(tool_name, arguments)
                
                # Add tool result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            
            # Get final response
            final_response = openai_client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                messages=messages
            )
            
            return final_response.choices[0].message.content
        
        # No tool calls, return response directly
        return message.content
        
    except Exception as e:
        logger.error(f"Error in chat_with_mcp_tools: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    app.run(debug=True, port=5000)