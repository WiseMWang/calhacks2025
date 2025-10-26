from flask import Flask, render_template, request, jsonify
import logging

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
        
        # For now, just echo back (replace with LLM later)
        response = f"Echo: {user_message}"
        
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

def get_mcp_tools():
    """Get available tools from MCP server"""
    try:
        # Start MCP server
        proc = subprocess.Popen(
            ['python', 'server/mcp_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Send tools/list request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        proc.stdin.write((json.dumps(request) + '\n').encode())
        proc.stdin.flush()
        
        # Read response
        response_line = proc.stdout.readline().decode()
        response = json.loads(response_line)
        
        proc.terminate()
        
        # Convert MCP tools to OpenAI format
        tools = []
        if 'result' in response and 'tools' in response['result']:
            for tool in response['result']['tools']:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool['name'],
                        "description": tool.get('description', ''),
                        "parameters": tool.get('parameters', {})
                    }
                })
        
        return tools
        
    except Exception as e:
        logger.error(f"Error getting MCP tools: {e}")
        return []

def call_mcp_tool(tool_name, arguments):
    """Call a tool via MCP server"""
    try:
        # Start MCP server
        proc = subprocess.Popen(
            ['python', 'server/mcp_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Send tool call request
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        proc.stdin.write((json.dumps(request) + '\n').encode())
        proc.stdin.flush()
        
        # Read response
        response_line = proc.stdout.readline().decode()
        response = json.loads(response_line)
        
        proc.terminate()
        
        if 'result' in response:
            # Extract text from content
            if 'content' in response['result']:
                content = response['result']['content']
                if isinstance(content, list) and len(content) > 0:
                    return content[0].get('text', str(content))
            return str(response['result'])
        
        return "Tool executed successfully"
        
    except Exception as e:
        logger.error(f"Error calling MCP tool: {e}")
        return f"Error: {str(e)}"

def chat_with_mcp_tools(user_message):
    """Chat with OpenAI using MCP tools"""
    try:
        # Get available tools
        tools = get_mcp_tools()
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
                result = call_mcp_tool(tool_name, arguments)
                
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