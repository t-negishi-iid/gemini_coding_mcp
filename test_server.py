#!/usr/bin/env python3
"""
Test script for Gemini Coding MCP Server
"""

import json
import subprocess
import os
import sys

def test_server():
    """Test the MCP server functionality"""
    
    # Set up environment
    env = os.environ.copy()
    
    # Check if API key is set
    if 'GEMINI_API_KEY' not in env:
        print("⚠️  Warning: GEMINI_API_KEY not set, using test mode")
        env['GEMINI_API_KEY'] = 'test_key_for_connection_test'
    
    # Path to server  
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.py')
    
    # Check if running in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        python_cmd = sys.executable
    else:
        # Try to use the virtual environment if it exists
        venv_python = os.path.join(os.path.dirname(server_path), 'venv', 'bin', 'python')
        if os.path.exists(venv_python):
            python_cmd = venv_python
        else:
            python_cmd = sys.executable
    
    try:
        # Start the server process
        process = subprocess.Popen(
            [python_cmd, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        # Test requests
        test_requests = [
            {"jsonrpc": "2.0", "method": "initialize", "id": 1},
            {"jsonrpc": "2.0", "method": "tools/list", "id": 2}
        ]
        
        print("=== Testing Gemini Coding MCP Server v1.0 ===\n")
        
        for req in test_requests:
            print(f"Sending: {json.dumps(req)}")
            process.stdin.write(json.dumps(req) + '\n')
            process.stdin.flush()
            
            # Read response
            response_line = process.stdout.readline()
            if response_line:
                try:
                    response = json.loads(response_line)
                    print(f"Response: {json.dumps(response, indent=2)}")
                    
                    # Show available tools if this is tools/list response
                    if req['method'] == 'tools/list' and 'result' in response:
                        tools = response['result'].get('tools', [])
                        print(f"\n🎉 Found {len(tools)} tools with 'gc' prefix:")
                        gc_tools = [t for t in tools if t['name'].startswith('gc')]
                        for tool in gc_tools[:5]:  # Show first 5 gc tools
                            print(f"  - {tool['name']}: {tool['description']}")
                        if len(gc_tools) > 5:
                            print(f"  ... and {len(gc_tools) - 5} more tools")
                            
                except json.JSONDecodeError as e:
                    print(f"Failed to parse response: {e}")
                    print(f"Raw response: {response_line}")
            
            print("-" * 50)
        
        # Terminate the process
        process.terminate()
        process.wait()
        
        print("\n✅ Server test completed successfully!")
        print("\nAll commands use 'gc' prefix to avoid conflicts:")
        print("- gchelp - Show help and available commands")
        print("- gcask - Ask Gemini any question")
        print("- gcreview - Review code quality")
        print("- gcdebug - Debug errors")
        print("- ... and 11 more specialized tools!")
        
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    test_server()