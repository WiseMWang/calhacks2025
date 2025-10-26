from flask import Flask, render_template, request, jsonify
import logging
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for MCP imports
parent_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, parent_dir)

try:
    from mcp.client.llm_client import LLMClient
except ImportError:
    # Fallback: add the specific client directory
    sys.path.insert(0, os.path.join(parent_dir, 'mcp', 'client'))
    from llm_client import LLMClient

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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
        
        # Use LLMClient for all LLM interactions
        response = asyncio.run(chat_with_llm_client(user_message))
        
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

async def chat_with_llm_client(user_message):
    """Chat using LLMClient with MCP tools"""
    try:
        # Create LLMClient instance
        llm_client = LLMClient()
        
        # Use LLMClient to handle the query with MCP server
        response = await llm_client.query(
            user_input=user_message,
            server_command="python",
            server_args=["server/mcp_server.py"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat_with_llm_client: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    app.run(debug=True, port=5005)