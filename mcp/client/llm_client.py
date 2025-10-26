import argparse
import openai
import subprocess
import json
import sys

class LLMClient:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)
    
    def get_mcp_tools(self):
        # Start MCP server and get tools
        result = subprocess.run([
            'python', 'server/mcp_server.py'
        ], input='{"method": "tools/list", "id": 1, "jsonrpc": "2.0"}', 
        text=True, capture_output=True)
        
        return json.loads(result.stdout)["result"]["tools"]
    
    def query(self, user_input):
        tools = self.get_mcp_tools()
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_input}],
            tools=[{"type": "function", "function": tool} for tool in tools]
        )
        
        return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(description="MCP LLM Client")
    parser.add_argument("query", help="Query to send to GPT-4")
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    
    args = parser.parse_args()
    
    client = LLMClient(args.api_key)
    result = client.query(args.query)
    print(result)

if __name__ == "__main__":
    main()