#!/usr/bin/env python3
"""
Gemini Coding MCP Server v1.0
IDE-friendly coding assistant with Gemini AI integration
"""

import json
import sys
import os
import hashlib
import time
from typing import Dict, Any, Optional
from pathlib import Path

# Ensure unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

# Server configuration
__version__ = "1.0.0"
SERVER_NAME = "gemini-coding"

# Simple in-memory cache for repeated queries
cache = {}
CACHE_TTL = 300  # 5 minutes
MAX_TEXT_LENGTH = 100000  # 100KB max input

# Initialize clipboard support
CLIPBOARD_AVAILABLE = False
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    pyperclip = None

# Initialize Gemini
try:
    import google.generativeai as genai
    
    # Get API key from environment variable only
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print(json.dumps({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": "Please set your Gemini API key in the GEMINI_API_KEY environment variable"
            }
        }), file=sys.stdout, flush=True)
        sys.exit(1)
    
    genai.configure(api_key=API_KEY)
    # Multiple models for different use cases
    model_pro = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')
    model_flash = genai.GenerativeModel('gemini-2.5-flash')
    GEMINI_AVAILABLE = True
except Exception as e:
    GEMINI_AVAILABLE = False
    GEMINI_ERROR = str(e)

def send_response(response: Dict[str, Any]):
    """Send a JSON-RPC response"""
    print(json.dumps(response), flush=True)

def handle_initialize(request_id: Any) -> Dict[str, Any]:
    """Handle initialization"""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": __version__
            }
        }
    }

def get_text_input(arguments: Dict[str, Any], text_param: str = "text") -> str:
    """
    Enhanced text input with multiple sources:
    1. Direct parameter (text, code, prompt, etc.)
    2. File path (file_path parameter)
    3. Environment variable (GEMINI_INPUT)
    4. Clipboard (if available and no other source)
    """
    
    # Method 1: Direct parameter
    direct_text = arguments.get(text_param, "").strip()
    if direct_text:
        return direct_text
    
    # Method 2: File path
    file_path = arguments.get("file_path", "").strip()
    if file_path:
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                content = path.read_text(encoding='utf-8')
                if len(content) > MAX_TEXT_LENGTH:
                    return content[:MAX_TEXT_LENGTH] + "\n\n[Content truncated at 100KB limit]"
                return content
            else:
                return f"Error: File not found: {file_path}"
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
    
    # Method 3: Environment variable
    env_text = os.environ.get("GEMINI_INPUT", "").strip()
    if env_text:
        return env_text
    
    # Method 4: Clipboard (fallback)
    if CLIPBOARD_AVAILABLE:
        try:
            clipboard_text = pyperclip.paste().strip()
            if clipboard_text and len(clipboard_text) > 10:  # Avoid empty or very short clipboard
                return clipboard_text
        except Exception:
            pass  # Clipboard access failed, continue
    
    # No input found
    return ""

def get_help_content(category: str = "all") -> str:
    """Generate help content for gc-prefixed commands"""
    
    basic_commands = """🚀 **BASIC COMMANDS**
• `gchelp` - Show this help (add category: basic, spec, code, debug)
• `gcask` - Ask Gemini any question
  Example: gcask prompt="How to optimize Python loops?"
  IDE Usage: Select text in editor → copy → gcask prompt="Explain this code"
"""

    spec_commands = """📋 **SPECIFICATION & DESIGN**
• `gcspec` - Analyze requirements and specifications  
  Example: gcspec specification="User auth with JWT" type="api"
  IDE Usage: gcspec file_path="requirements.md"
• `gcarch` - Review system architecture
  Example: gcarch architecture="Microservices with Docker"
  IDE Usage: Copy architecture diagram → gcarch focus="scalability"
• `gcapi` - Design API interfaces
  Example: gcapi type="REST" requirements="User CRUD operations"
"""

    code_commands = """💻 **CODE ANALYSIS & IMPROVEMENT**
• `gcreview` - Review code quality
  Example: gcreview file_path="src/auth.py" focus="security"
  IDE Usage: Select code → copy → gcreview focus="performance"
• `gcrefactor` - Suggest code improvements
  Example: gcrefactor goal="readability" file_path="legacy.py"
  IDE Usage: Select function → copy → gcrefactor goal="performance"
• `gcperf` - Analyze code performance
  Example: gcperf file_path="slow_function.py"
  IDE Usage: Copy slow code → gcperf context="database"
• `gcsecurity` - Security audit
  Example: gcsecurity file_path="login.py" level="enterprise"
  IDE Usage: Select auth code → copy → gcsecurity level="critical"
• `gctest` - Generate test strategies
  Example: gctest file_path="utils.py" type="unit"
  IDE Usage: Copy function → gctest type="integration"
"""

    debug_commands = """🔍 **DEBUG & UNDERSTANDING**
• `gcdebug` - Debug errors and issues
  Example: gcdebug error="TypeError: 'str' not callable"
  IDE Usage: Copy error from terminal → gcdebug
• `gcexplain` - Explain code functionality
  Example: gcexplain file_path="complex.py" level="beginner"
  IDE Usage: Select complex code → copy → gcexplain level="advanced"
"""

    utility_commands = """🛠️ **UTILITY TOOLS**
• `gcdeps` - Analyze project dependencies
  Example: gcdeps file_path="package.json" focus="security"
• `gccomplete` - Complete code with AI
  Example: gccomplete context="class User:" request="add login method"
  IDE Usage: Select partial code → copy to context → gccomplete request="finish this"
• `gcdocs` - Generate documentation
  Example: gcdocs file_path="api.py" type="readme"
  IDE Usage: Select functions → copy → gcdocs type="api"
"""

    ide_usage = """💡 **IDE WORKFLOW TIPS**
• All commands support multiple input methods:
  1. Direct text: gcask prompt="your question"
  2. File path: gcreview file_path="/path/to/file.py"
  3. Environment variable: GEMINI_INPUT="text" gcask
  4. Clipboard: Copy text in IDE → run command without text param

• Common IDE workflows:
  - Select code → Copy → gcreview (auto-uses clipboard)
  - Copy error message → gcdebug (auto-uses clipboard)  
  - gcexplain file_path="complex_file.py" (reads entire file)
  - Use GEMINI_INPUT for IDE extensions

• Commands are prefixed with 'gc' to avoid conflicts with other tools
"""

    categories = {
        "basic": basic_commands,
        "spec": spec_commands, 
        "code": code_commands,
        "debug": debug_commands,
        "utility": utility_commands,
        "ide": ide_usage,
        "all": basic_commands + spec_commands + code_commands + debug_commands + utility_commands + ide_usage
    }
    
    help_text = f"""
# 🤖 Gemini Coding MCP Server v{__version__}

{categories.get(category, categories["all"])}

🔗 **Quick Examples:**
- `gcask prompt="Best Python frameworks"`
- `gcreview focus="security"` (uses clipboard)
- `gcdebug` (uses clipboard for error)
- `gchelp category=ide` (IDE workflow tips)
"""
    
    return help_text

def handle_tools_list(request_id: Any) -> Dict[str, Any]:
    """List available tools with gc-prefixed names for conflict avoidance"""
    tools = []
    
    if GEMINI_AVAILABLE:
        tools = [
            # Essential Tools - GC-prefixed to avoid conflicts
            {
                "name": "gchelp",
                "description": "Show available commands and usage examples",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Category to show help for (basic, spec, code, debug, ide, all)", "default": "all"}
                    }
                }
            },
            {
                "name": "gcask",
                "description": "Ask Gemini any question (supports clipboard/file input)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Your question (or leave empty to use clipboard/env/file)"},
                        "file_path": {"type": "string", "description": "Path to file to read as input"},
                        "fast": {"type": "boolean", "description": "Use faster model", "default": False}
                    }
                }
            },
            
            # Specification & Design
            {
                "name": "gcspec",
                "description": "Analyze requirements and specifications",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "specification": {"type": "string", "description": "The specification to analyze (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to specification file"},
                        "type": {"type": "string", "description": "Type (api, feature, system)", "default": "general"}
                    }
                }
            },
            {
                "name": "gcarch",
                "description": "Review system architecture",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "architecture": {"type": "string", "description": "Architecture description (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to architecture file"},
                        "focus": {"type": "string", "description": "Focus area (scalability, security, performance)", "default": "general"}
                    }
                }
            },
            {
                "name": "gcapi",
                "description": "Design API interfaces",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "description": "API type (REST, GraphQL, etc.)"},
                        "requirements": {"type": "string", "description": "API requirements (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to requirements file"}
                    },
                    "required": ["type"]
                }
            },
            
            # Code Analysis & Improvement
            {
                "name": "gcreview",
                "description": "Review code quality and best practices",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to review (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to code file"},
                        "focus": {"type": "string", "description": "Focus (security, performance, style)", "default": "general"}
                    }
                }
            },
            {
                "name": "gcrefactor",
                "description": "Suggest code improvements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to refactor (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to code file"},
                        "goal": {"type": "string", "description": "Goal (readability, performance, maintainability)"}
                    },
                    "required": ["goal"]
                }
            },
            {
                "name": "gcperf",
                "description": "Analyze code performance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to analyze (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to code file"},
                        "context": {"type": "string", "description": "Performance context", "default": "general"}
                    }
                }
            },
            {
                "name": "gcsecurity",
                "description": "Security audit and vulnerability analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to audit (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to code file"},
                        "level": {"type": "string", "description": "Security level (basic, enterprise, critical)", "default": "basic"}
                    }
                }
            },
            {
                "name": "gctest",
                "description": "Generate test strategies and cases",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to test (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to code file"},
                        "type": {"type": "string", "description": "Test type (unit, integration, e2e)", "default": "unit"}
                    }
                }
            },
            
            # Debug & Understanding
            {
                "name": "gcdebug",
                "description": "Debug errors and issues",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string", "description": "Error message or stack trace (or use clipboard)"},
                        "context": {"type": "string", "description": "Code context", "default": ""}
                    }
                }
            },
            {
                "name": "gcexplain",
                "description": "Explain code functionality",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to explain (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to code file"},
                        "level": {"type": "string", "description": "Level (beginner, intermediate, advanced)", "default": "intermediate"}
                    }
                }
            },
            
            # Utility Tools
            {
                "name": "gcdeps",
                "description": "Analyze project dependencies",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dependencies": {"type": "string", "description": "Dependencies list (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to package.json, requirements.txt, etc."},
                        "focus": {"type": "string", "description": "Focus (security, performance, size)", "default": "general"}
                    }
                }
            },
            {
                "name": "gccomplete",
                "description": "Complete code with AI assistance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "context": {"type": "string", "description": "Existing code context (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to context file"},
                        "request": {"type": "string", "description": "What to complete"}
                    },
                    "required": ["request"]
                }
            },
            {
                "name": "gcdocs",
                "description": "Generate documentation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Code to document (or use file_path/clipboard)"},
                        "file_path": {"type": "string", "description": "Path to code file"},
                        "type": {"type": "string", "description": "Doc type (api, readme, inline)", "default": "comprehensive"}
                    }
                }
            }
        ]
    else:
        tools = [
            {
                "name": "server_info",
                "description": "Get server status and error information",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": tools
        }
    }

def get_cache_key(prompt: str, temperature: float, use_fast_model: bool) -> str:
    """Generate cache key for the request"""
    cache_string = f"{prompt}_{temperature}_{use_fast_model}"
    return hashlib.md5(cache_string.encode()).hexdigest()

def call_gemini(prompt: str, temperature: float = 0.5, use_fast_model: bool = False, max_tokens: int = 8192, use_cache: bool = True) -> str:
    """Call Gemini and return response with caching support"""
    
    # Check cache first if enabled
    if use_cache:
        cache_key = get_cache_key(prompt, temperature, use_fast_model)
        if cache_key in cache:
            cached_entry = cache[cache_key]
            if time.time() - cached_entry['timestamp'] < CACHE_TTL:
                return cached_entry['response']
            else:
                # Remove expired entry
                del cache[cache_key]
    
    try:
        model = model_flash if use_fast_model else model_pro
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        
        result = response.text
        
        # Cache the response if caching is enabled and temperature is low (more deterministic)
        if use_cache and temperature <= 0.3:
            cache_key = get_cache_key(prompt, temperature, use_fast_model)
            cache[cache_key] = {
                'response': result,
                'timestamp': time.time()
            }
            
            # Simple cache cleanup - remove oldest entries if cache gets too large
            if len(cache) > 100:
                oldest_key = min(cache.keys(), key=lambda k: cache[k]['timestamp'])
                del cache[oldest_key]
        
        return result
        
    except Exception as e:
        # Enhanced error handling with retry logic
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate" in error_msg.lower():
            return f"Rate limit exceeded. Please try again in a few moments. Error: {error_msg}"
        elif "api" in error_msg.lower() and "key" in error_msg.lower():
            return f"API key issue. Please check your Gemini API key configuration. Error: {error_msg}"
        else:
            return f"Error calling Gemini: {error_msg}"

def handle_tool_call(request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool execution with gc-prefixed command names and enhanced input"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    try:
        result = ""
        
        if tool_name == "server_info":
            if GEMINI_AVAILABLE:
                clipboard_status = "enabled" if CLIPBOARD_AVAILABLE else "disabled (install pyperclip)"
                result = f"Gemini Coding MCP Server v{__version__} - Connected and ready with 15 IDE-friendly tools! Clipboard support: {clipboard_status}"
            else:
                result = f"Server v{__version__} - Gemini error: {GEMINI_ERROR}"
        
        # Help command
        elif tool_name == "gchelp":
            category = arguments.get("category", "all")
            result = get_help_content(category)
        
        # Basic tools
        elif tool_name == "gcask":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                prompt = get_text_input(arguments, "prompt")
                if not prompt:
                    result = "No input provided. Please use: prompt parameter, file_path, GEMINI_INPUT env var, or clipboard."
                else:
                    use_fast_model = arguments.get("fast", False)
                    result = call_gemini(prompt, 0.5, use_fast_model)
        
        # Specification & Design Tools
        elif tool_name == "gcspec":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                spec = get_text_input(arguments, "specification")
                if not spec:
                    result = "No specification provided. Use specification parameter, file_path, or clipboard."
                else:
                    spec_type = arguments.get("type", "general")
                    prompt = f"""As a requirements analyst, analyze this {spec_type} specification:

{spec}

Provide analysis covering:
1. Completeness - what's missing or unclear?
2. Consistency - any contradictions?
3. Testability - can requirements be verified?
4. Feasibility - technical considerations
5. Clarity - areas needing clarification
6. Recommendations for improvement"""
                    result = call_gemini(prompt, 0.2)
        
        elif tool_name == "gcarch":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                arch_desc = get_text_input(arguments, "architecture")
                if not arch_desc:
                    result = "No architecture description provided. Use architecture parameter, file_path, or clipboard."
                else:
                    focus = arguments.get("focus", "general")
                    prompt = f"""As a software architect, analyze this architecture with focus on {focus}:

{arch_desc}

Provide analysis covering:
1. Strengths and weaknesses
2. Scalability considerations  
3. Performance implications
4. Security architecture
5. Maintainability concerns
6. Improvement recommendations
7. Alternative patterns to consider"""
                    result = call_gemini(prompt, 0.3)
        
        elif tool_name == "gcapi":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                api_type = arguments.get("type", "")
                requirements = get_text_input(arguments, "requirements")
                if not requirements:
                    result = "No API requirements provided. Use requirements parameter, file_path, or clipboard."
                else:
                    prompt = f"""As an API design expert, design a {api_type} API:

Requirements: {requirements}

Provide:
1. API structure and endpoints
2. Data models and schemas
3. Authentication approach
4. Error handling strategy
5. Example requests/responses
6. Best practices implementation"""
                    result = call_gemini(prompt, 0.2)
        
        # Code Analysis Tools
        elif tool_name == "gcreview":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                code = get_text_input(arguments, "code")
                if not code:
                    result = "No code provided. Use code parameter, file_path, or clipboard."
                else:
                    focus = arguments.get("focus", "general")
                    prompt = f"""As an expert code reviewer, analyze this code with focus on {focus}:

```
{code}
```

Provide structured feedback:
1. Code quality and potential bugs
2. Security vulnerabilities
3. Performance opportunities
4. Best practices adherence
5. Maintainability improvements
6. Specific recommendations with examples"""
                    result = call_gemini(prompt, 0.2)
        
        elif tool_name == "gcrefactor":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                code = get_text_input(arguments, "code")
                goal = arguments.get("goal", "")
                if not code:
                    result = "No code provided. Use code parameter, file_path, or clipboard."
                elif not goal:
                    result = "No refactoring goal specified. Please provide a goal (readability, performance, maintainability, etc.)"
                else:
                    prompt = f"""As a refactoring expert, improve this code for {goal}:

```
{code}
```

Provide:
1. Specific refactoring recommendations
2. Before/after code examples
3. Explanation of improvements
4. Impact on {goal}
5. Step-by-step approach
6. Testing considerations"""
                    result = call_gemini(prompt, 0.2)
        
        elif tool_name == "gcperf":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                code = get_text_input(arguments, "code")
                if not code:
                    result = "No code provided. Use code parameter, file_path, or clipboard."
                else:
                    context = arguments.get("context", "general")
                    prompt = f"""As a performance expert, analyze this code for {context} performance:

```
{code}
```

Provide analysis:
1. Performance bottlenecks
2. Time/space complexity
3. Optimization recommendations
4. Optimized code examples
5. Profiling strategies
6. Scalability considerations"""
                    result = call_gemini(prompt, 0.2)
        
        elif tool_name == "gcsecurity":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                code = get_text_input(arguments, "code")
                if not code:
                    result = "No code provided. Use code parameter, file_path, or clipboard."
                else:
                    level = arguments.get("level", "basic")
                    prompt = f"""As a security expert, audit this code for {level}-level security:

```
{code}
```

Provide security analysis:
1. Vulnerability identification
2. Input validation issues
3. Authentication/authorization flaws
4. Data exposure risks
5. Injection attack vectors
6. Remediation recommendations
7. Security testing strategies"""
                    result = call_gemini(prompt, 0.1)
        
        elif tool_name == "gctest":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                code = get_text_input(arguments, "code")
                if not code:
                    result = "No code provided. Use code parameter, file_path, or clipboard."
                else:
                    test_type = arguments.get("type", "unit")
                    prompt = f"""As a testing expert, create {test_type} testing strategy:

```
{code}
```

Provide:
1. Test plan and strategy
2. Specific test cases
3. Edge cases and boundaries
4. Mock/stub strategies
5. Test data requirements
6. Framework recommendations
7. Coverage expectations"""
                    result = call_gemini(prompt, 0.3)
        
        # Debug & Understanding Tools
        elif tool_name == "gcdebug":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                error_msg = get_text_input(arguments, "error")
                if not error_msg:
                    result = "No error message provided. Use error parameter or clipboard."
                else:
                    context = arguments.get("context", "")
                    prompt = f"""As a debugging expert, help solve this error:

Error: {error_msg}
Context: {context}

Provide:
1. Root cause analysis
2. Step-by-step debugging approach
3. Specific solutions with examples
4. Prevention strategies
5. Debugging tools to use
6. Common variations of this error"""
                    result = call_gemini(prompt, 0.2)
        
        elif tool_name == "gcexplain":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                code = get_text_input(arguments, "code")
                if not code:
                    result = "No code provided. Use code parameter, file_path, or clipboard."
                else:
                    level = arguments.get("level", "intermediate")
                    prompt = f"""As a code mentor, explain this code at {level} level:

```
{code}
```

Provide explanation:
1. High-level purpose and functionality
2. Step-by-step logic breakdown
3. Key concepts and patterns
4. Data and control flow
5. Important design decisions
6. Potential gotchas
7. Related concepts to learn"""
                    result = call_gemini(prompt, 0.3)
        
        # Utility Tools
        elif tool_name == "gcdeps":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                dependencies = get_text_input(arguments, "dependencies")
                if not dependencies:
                    result = "No dependencies provided. Use dependencies parameter, file_path, or clipboard."
                else:
                    focus = arguments.get("focus", "general")
                    prompt = f"""As a dependency expert, analyze these dependencies for {focus}:

{dependencies}

Provide analysis:
1. Security vulnerability assessment
2. Maintenance and community health
3. Performance impact
4. Size and bundle analysis
5. Alternative recommendations
6. Version compatibility
7. License compliance
8. Upgrade suggestions"""
                    result = call_gemini(prompt, 0.2)
        
        elif tool_name == "gccomplete":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                context = get_text_input(arguments, "context")
                request = arguments.get("request", "")
                if not request:
                    result = "No completion request specified. Please provide what you want to complete."
                else:
                    prompt = f"""As a code completion expert, complete this code:

Context:
```
{context}
```

Request: {request}

Provide:
1. Complete implementation
2. Explanation of approach
3. Alternative options
4. Best practices incorporated
5. Error handling
6. Testing suggestions"""
                    result = call_gemini(prompt, 0.2)
        
        elif tool_name == "gcdocs":
            if not GEMINI_AVAILABLE:
                result = f"Gemini not available: {GEMINI_ERROR}"
            else:
                code = get_text_input(arguments, "code")
                if not code:
                    result = "No code provided. Use code parameter, file_path, or clipboard."
                else:
                    doc_type = arguments.get("type", "comprehensive")
                    prompt = f"""As a documentation expert, create {doc_type} documentation:

```
{code}
```

Generate documentation:
1. Clear overview and purpose
2. Installation/setup instructions
3. Usage examples
4. API reference
5. Configuration options
6. Common use cases
7. Troubleshooting guide"""
                    result = call_gemini(prompt, 0.3)
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"🤖 GEMINI RESPONSE:\n\n{result}"
                    }
                ]
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }

def main():
    """Main server loop"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            if method == "initialize":
                response = handle_initialize(request_id)
            elif method == "tools/list":
                response = handle_tools_list(request_id)
            elif method == "tools/call":
                response = handle_tool_call(request_id, params)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            send_response(response)
            
        except json.JSONDecodeError:
            continue
        except EOFError:
            break
        except Exception as e:
            if 'request_id' in locals():
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                })

if __name__ == "__main__":
    main()