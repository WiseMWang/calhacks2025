from flask import Flask, render_template, request, jsonify
import logging
import asyncio
import os
from mcp.client.llm_client import run_llm_query

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
        
        # Get OpenAI API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not found. Set OPENAI_API_KEY environment variable.'
            }), 500
        
        # Run LLM query with MCP integration
        response = asyncio.run(run_llm_query(user_message, api_key))
        
        return jsonify({
            'success': True,
            'response': response
        })
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)