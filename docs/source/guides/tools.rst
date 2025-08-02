Tools Guide
===========

Tools extend agent capabilities beyond language processing, enabling interaction with external systems, code execution, and data manipulation.

Understanding Tools
-------------------

Tools in Pantheon provide:

- **Capabilities**: Specific functions agents can perform
- **Safety**: Controlled access to system resources
- **Extensibility**: Easy creation of custom tools
- **Async Support**: Non-blocking operations

Tool Architecture
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.tools import Tool
   
   class CustomTool(Tool):
       name = "custom_tool"
       description = "What this tool does"
       
       async def execute(self, **kwargs):
           # Tool implementation
           return result

Built-in Tools
--------------

PythonTools
~~~~~~~~~~~

Execute Python code in isolated environments.

**Basic Usage**:

.. code-block:: python

   from pantheon.tools import PythonTools
   
   python_tool = PythonTools()
   
   # Simple execution
   result = await python_tool.execute(
       code="print('Hello World')"
   )

**Advanced Configuration**:

.. code-block:: python

   python_tool = PythonTools(
       # Sandbox settings
       sandbox=True,
       timeout=300,  # 5 minutes
       memory_limit="512MB",
       
       # Available packages
       packages=["numpy", "pandas", "matplotlib"],
       
       # Custom imports
       pre_imports=[
           "import numpy as np",
           "import pandas as pd"
       ],
       
       # Persistent session
       persistent=True,
       session_id="analysis_session"
   )

**Security Features**:

.. code-block:: python

   secure_python = PythonTools(
       # Restrict imports
       forbidden_imports=["os", "subprocess", "eval"],
       
       # Network restrictions
       allow_network=False,
       
       # File system access
       fs_access="read_only",
       allowed_paths=["./data"],
       
       # Resource limits
       max_execution_time=60,
       max_memory="256MB",
       max_output_size="10MB"
   )

RTools
~~~~~~

Statistical computing with R.

.. code-block:: python

   from pantheon.tools import RTools
   
   r_tool = RTools(
       packages=["ggplot2", "dplyr", "tidyr"],
       workspace="./r_workspace"
   )
   
   result = await r_tool.execute(
       code="""
       library(ggplot2)
       data <- data.frame(x=1:10, y=rnorm(10))
       p <- ggplot(data, aes(x=x, y=y)) + geom_line()
       ggsave("plot.png", p)
       """
   )

ShellTools
~~~~~~~~~~

Execute shell commands safely.

**Basic Usage**:

.. code-block:: python

   from pantheon.tools import ShellTools
   
   shell = ShellTools()
   
   # List files
   result = await shell.execute(command="ls -la")

**Safety Configuration**:

.. code-block:: python

   safe_shell = ShellTools(
       # Allowed commands whitelist
       allowed_commands=["ls", "grep", "find", "cat"],
       
       # Forbidden patterns
       forbidden_patterns=[
           r"rm\s+-rf",
           r"sudo",
           r"chmod\s+777"
       ],
       
       # Path restrictions
       allowed_paths=["./workspace", "/tmp"],
       forbidden_paths=["/etc", "/sys", "/root"],
       
       # Environment
       env_vars={"CUSTOM_VAR": "value"},
       inherit_env=False,
       
       # Limits
       timeout=30,
       max_output_size="1MB"
   )

WebTools
~~~~~~~~

Web searching and content fetching.

**Search Operations**:

.. code-block:: python

   from pantheon.tools import WebTools
   
   web = WebTools(
       search_engines=["google", "bing", "duckduckgo"],
       max_results=10,
       safe_search=True
   )
   
   # Search the web
   results = await web.search(
       query="Python async programming",
       num_results=5,
       search_type="web"  # or "news", "scholar"
   )

**Content Fetching**:

.. code-block:: python

   # Fetch and parse content
   content = await web.fetch(
       url="https://example.com",
       parse_format="markdown",  # or "text", "html"
       include_metadata=True,
       follow_redirects=True,
       timeout=30
   )

**Advanced Features**:

.. code-block:: python

   advanced_web = WebTools(
       # Caching
       cache_enabled=True,
       cache_ttl=3600,  # 1 hour
       
       # Rate limiting
       rate_limit="10/minute",
       
       # Headers
       headers={"User-Agent": "Pantheon-Agent/1.0"},
       
       # Proxy support
       proxy="http://proxy.example.com:8080",
       
       # Content filtering
       content_filters={
           "min_length": 100,
           "max_length": 50000,
           "language": "en"
       }
   )

FileTools
~~~~~~~~~

File system operations.

**Basic Operations**:

.. code-block:: python

   from pantheon.tools import FileTools
   
   files = FileTools(
       base_path="./workspace",
       allowed_operations=["read", "write", "create", "delete"]
   )
   
   # Read file
   content = await files.read("data.txt")
   
   # Write file
   await files.write("output.txt", "Hello World")
   
   # List directory
   files_list = await files.list_dir("./")

**Advanced Configuration**:

.. code-block:: python

   secure_files = FileTools(
       # Path restrictions
       allowed_paths=["./data", "./output"],
       forbidden_paths=["./config", "./secrets"],
       
       # File type restrictions
       allowed_extensions=[".txt", ".csv", ".json"],
       forbidden_extensions=[".exe", ".sh", ".bat"],
       
       # Size limits
       max_file_size="10MB",
       max_total_size="100MB",
       
       # Permissions
       file_permissions="644",
       directory_permissions="755",
       
       # Encoding
       default_encoding="utf-8",
       detect_encoding=True
   )

DatabaseTools
~~~~~~~~~~~~~

Database interactions.

.. code-block:: python

   from pantheon.tools import DatabaseTools
   
   db = DatabaseTools(
       connections={
           "main": "postgresql://user:pass@localhost/db",
           "analytics": "mysql://user:pass@localhost/analytics"
       },
       default_connection="main"
   )
   
   # Query execution
   results = await db.query(
       "SELECT * FROM users WHERE created_at > %s",
       params=["2024-01-01"],
       connection="main"
   )
   
   # Safe operations
   safe_db = DatabaseTools(
       read_only=True,
       allowed_tables=["users", "products"],
       forbidden_operations=["DROP", "TRUNCATE", "DELETE"],
       query_timeout=30,
       row_limit=1000
   )

Creating Custom Tools
---------------------

Basic Custom Tool
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.tools import Tool
   
   class WeatherTool(Tool):
       name = "weather"
       description = "Get weather information for a location"
       
       def __init__(self, api_key: str):
           super().__init__()
           self.api_key = api_key
       
       async def execute(self, location: str, units: str = "metric"):
           # Implementation
           response = await self.fetch_weather(location, units)
           return self.format_response(response)
       
       async def fetch_weather(self, location, units):
           # API call implementation
           pass
       
       def format_response(self, data):
           return f"Weather in {data['location']}: {data['temp']}°"

Advanced Custom Tool
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.tools import Tool, ToolResult, ToolError
   from typing import Dict, Any
   import aiohttp
   
   class TranslationTool(Tool):
       name = "translator"
       description = "Translate text between languages"
       
       # Tool metadata
       metadata = {
           "version": "1.0.0",
           "author": "Your Name",
           "requires_auth": True,
           "rate_limited": True
       }
       
       # Parameter schema
       parameters = {
           "text": {"type": "string", "required": True},
           "source_lang": {"type": "string", "default": "auto"},
           "target_lang": {"type": "string", "required": True}
       }
       
       def __init__(self, api_key: str, **kwargs):
           super().__init__(**kwargs)
           self.api_key = api_key
           self.session = None
       
       async def initialize(self):
           """Initialize resources"""
           self.session = aiohttp.ClientSession()
       
       async def cleanup(self):
           """Clean up resources"""
           if self.session:
               await self.session.close()
       
       async def execute(self, **kwargs) -> ToolResult:
           try:
               # Validate parameters
               self.validate_params(kwargs)
               
               # Perform translation
               result = await self._translate(
                   text=kwargs["text"],
                   source=kwargs.get("source_lang", "auto"),
                   target=kwargs["target_lang"]
               )
               
               return ToolResult(
                   success=True,
                   data=result,
                   metadata={
                       "chars_translated": len(kwargs["text"]),
                       "detected_lang": result.get("detected_language")
                   }
               )
               
           except Exception as e:
               return ToolResult(
                   success=False,
                   error=ToolError(
                       type="translation_error",
                       message=str(e)
                   )
               )

Tool Composition
~~~~~~~~~~~~~~~~

Combine multiple tools:

.. code-block:: python

   from pantheon.tools import ComposedTool
   
   class DataAnalysisTool(ComposedTool):
       """Combines file reading, data processing, and visualization"""
       
       sub_tools = {
           "file": FileTools(),
           "python": PythonTools(packages=["pandas", "matplotlib"]),
           "web": WebTools()
       }
       
       async def execute(self, task: str):
           # Step 1: Read data
           if "file:" in task:
               data = await self.sub_tools["file"].read(...)
           elif "url:" in task:
               data = await self.sub_tools["web"].fetch(...)
           
           # Step 2: Process with Python
           result = await self.sub_tools["python"].execute(
               code=f"analyze_data({data})"
           )
           
           return result

Tool Safety and Security
------------------------

Input Validation
~~~~~~~~~~~~~~~~

.. code-block:: python

   class SecureTool(Tool):
       def validate_params(self, params: Dict[str, Any]):
           # Type checking
           if not isinstance(params.get("query"), str):
               raise ValueError("Query must be a string")
           
           # Length limits
           if len(params["query"]) > 1000:
               raise ValueError("Query too long")
           
           # Pattern matching
           if self.contains_forbidden_patterns(params["query"]):
               raise ValueError("Query contains forbidden content")
           
           # Sanitization
           params["query"] = self.sanitize_input(params["query"])

Resource Limits
~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.tools import ResourceLimiter
   
   class LimitedTool(Tool):
       def __init__(self):
           super().__init__()
           self.limiter = ResourceLimiter(
               max_memory="512MB",
               max_cpu_time=60,
               max_concurrent=5,
               rate_limit="100/hour"
           )
       
       async def execute(self, **kwargs):
           async with self.limiter:
               return await self._execute_impl(**kwargs)

Access Control
~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.tools import AccessControl
   
   class RestrictedTool(Tool):
       def __init__(self):
           super().__init__()
           self.access_control = AccessControl(
               allowed_users=["agent1", "agent2"],
               required_permissions=["read", "write"],
               ip_whitelist=["192.168.1.0/24"],
               time_restrictions={
                   "business_hours_only": True,
                   "timezone": "UTC"
               }
           )
       
       async def execute(self, **kwargs):
           # Check access
           if not self.access_control.check_access(kwargs.get("user")):
               raise PermissionError("Access denied")
           
           return await self._execute_impl(**kwargs)

Tool Testing
------------

Unit Testing
~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from pantheon.tools import MockTool
   
   @pytest.mark.asyncio
   async def test_custom_tool():
       # Create tool instance
       tool = WeatherTool(api_key="test_key")
       
       # Mock external calls
       with MockTool(tool) as mock:
           mock.set_response({"temp": 25, "location": "London"})
           
           # Test execution
           result = await tool.execute(location="London")
           assert "25°" in result
           assert "London" in result

Integration Testing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   @pytest.mark.integration
   async def test_tool_with_agent():
       # Create tool and agent
       tool = CustomTool()
       agent = Agent(
           name="TestAgent",
           tools=[tool]
       )
       
       # Test tool usage by agent
       result = await agent.execute("Use the custom tool")
       assert result.success
       assert tool.call_count == 1

Performance Testing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import asyncio
   import time
   
   async def test_tool_performance():
       tool = DataProcessingTool()
       
       # Measure execution time
       start = time.time()
       tasks = [
           tool.execute(data=f"dataset_{i}")
           for i in range(100)
       ]
       results = await asyncio.gather(*tasks)
       duration = time.time() - start
       
       assert duration < 10  # Should complete in 10 seconds
       assert all(r.success for r in results)

Tool Best Practices
-------------------

1. **Clear Purpose**: Each tool should have a single, well-defined purpose
2. **Error Handling**: Always handle and report errors gracefully
3. **Resource Management**: Clean up resources in finally blocks
4. **Async First**: Design tools to be async from the start
5. **Security**: Validate all inputs and limit resource usage
6. **Documentation**: Provide clear descriptions and examples
7. **Testing**: Write comprehensive tests for all tools
8. **Monitoring**: Add logging and metrics collection

Tool Registry
-------------

Register and discover tools:

.. code-block:: python

   from pantheon.tools import ToolRegistry
   
   # Global registry
   registry = ToolRegistry()
   
   # Register tools
   registry.register(WeatherTool)
   registry.register(TranslationTool)
   
   # Discover tools
   available_tools = registry.list_tools()
   weather_tool = registry.get_tool("weather")
   
   # Tool categories
   web_tools = registry.get_by_category("web")
   data_tools = registry.get_by_category("data")

Next Steps
----------

- Review :doc:`agents` to use tools with agents
- Explore :doc:`memory` for tool state persistence
- Check :doc:`distributed` for remote tool execution
- See :doc:`../examples/custom_tools` for more examples