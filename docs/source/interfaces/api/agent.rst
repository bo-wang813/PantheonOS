Agent API
=========

The Agent class is the fundamental building block of Pantheon.

.. autoclass:: pantheon.agent.Agent
   :members: run, chat, stream
   :undoc-members:

Creating an Agent
-----------------

**Basic Agent**

.. code-block:: python

   from pantheon import Agent

   agent = Agent(
       name="assistant",
       instructions="You are a helpful assistant.",
       model="gpt-4o-mini"
   )

**With Toolsets**

.. code-block:: python

   from pantheon.toolsets import FileManagerToolSet, ShellToolSet

   agent = Agent(
       name="developer",
       instructions="You are a developer.",
       model="gpt-4o"
   )

   # Add toolsets using await agent.toolset()
   await agent.toolset(FileManagerToolSet("files"))
   await agent.toolset(ShellToolSet("shell"))

**With Memory**

.. code-block:: python

   agent = Agent(
       name="assistant",
       instructions="...",
       use_memory=True
   )

Constructor Parameters
----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Parameter
     - Type
     - Description
   * - ``name``
     - str
     - Agent name (used for identification)
   * - ``instructions``
     - str
     - System prompt defining agent behavior
   * - ``model``
     - str
     - LLM model to use (e.g., "gpt-4o", "claude-3-opus")
   * - ``tools``
     - list[Callable]
     - List of callable functions (for ToolSets, use ``await agent.toolset()``)
   * - ``use_memory``
     - bool
     - Enable conversation persistence
   * - ``max_iterations``
     - int
     - Maximum tool call iterations (default: 10)

Methods
-------

run()
~~~~~

Execute a single query and return the response.

.. code-block:: python

   response = await agent.run("What is 2 + 2?")
   print(response.content)

**Parameters:**

- ``message`` (str): The user message

**Returns:** ``AgentResponse``

chat()
~~~~~~

Start an interactive REPL session.

.. code-block:: python

   await agent.chat()

stream()
~~~~~~~~

Stream the response token by token.

.. code-block:: python

   async for chunk in agent.stream("Tell me a story"):
       print(chunk.content, end="")

toolset()
~~~~~~~~~

Add a toolset to the agent at runtime.

.. code-block:: python

   from pantheon.toolsets import FileManagerToolSet, ShellToolSet

   agent = Agent(
       name="developer",
       instructions="You are a developer.",
       model="gpt-4o"
   )

   # Add toolsets dynamically
   await agent.toolset(FileManagerToolSet("files"))
   await agent.toolset(ShellToolSet("shell"))

**Parameters:**

- ``toolset`` (ToolSet | ToolProvider): The toolset or provider to add

**Returns:** ``Agent`` (for method chaining)

mcp()
~~~~~

Add an MCP (Model Context Protocol) provider to the agent.

.. code-block:: python

   from pantheon.providers import MCPProvider

   # Add MCP provider
   await agent.mcp(
       name="custom_tools",
       provider=MCPProvider(uri="stdio://path/to/mcp/server")
   )

**Parameters:**

- ``name`` (str): Name for the MCP provider
- ``provider`` (ToolProvider): The MCP provider instance

**Returns:** ``Agent`` (for method chaining)

AgentResponse
-------------

The response object returned by ``run()``:

.. code-block:: python

   response = await agent.run("...")

   # Content
   print(response.content)

   # Messages (full conversation)
   print(response.messages)

   # Tool calls made
   print(response.tool_calls)

   # Token usage
   print(response.usage)

Custom Tools
------------

**Using Decorator**

.. code-block:: python

   @agent.tool
   def my_function(param: str) -> str:
       """Description for the LLM."""
       return f"Result: {param}"

**Using ToolSet**

.. code-block:: python

   from pantheon.toolset import ToolSet, tool

   class MyTools(ToolSet):
       def __init__(self, name: str):
           super().__init__(name)

       @tool
       def calculate(self, expression: str) -> float:
           """Evaluate math expression."""
           return eval(expression)

   # Add toolset at runtime
   agent = Agent(name="calculator", instructions="...", model="gpt-4o")
   await agent.toolset(MyTools("math"))

Model Selection
---------------

Specify models using provider prefixes:

.. code-block:: python

   # OpenAI
   agent = Agent(model="gpt-4o")
   agent = Agent(model="openai/gpt-4o-mini")

   # Anthropic
   agent = Agent(model="claude-3-opus")
   agent = Agent(model="anthropic/claude-3-sonnet")

   # Other providers (via LiteLLM)
   agent = Agent(model="gemini/gemini-pro")

Best Practices
--------------

**Clear Instructions**

Write specific, clear instructions:

.. code-block:: python

   agent = Agent(
       instructions="""You are a Python developer assistant.

       Your responsibilities:
       - Write clean, well-documented code
       - Follow PEP 8 style guidelines
       - Include error handling

       When asked to write code:
       1. First explain your approach
       2. Write the code
       3. Explain how to use it"""
   )

**Appropriate Model**

- Use ``gpt-4o-mini`` for simple tasks (faster, cheaper)
- Use ``gpt-4o`` or ``claude-3-opus`` for complex tasks

**Tool Selection**

Only include tools the agent needs:

.. code-block:: python

   # Good - specific tools
   agent = Agent(name="dev", instructions="...", model="gpt-4o")
   await agent.toolset(FileManagerToolSet("files"))

   # Avoid - too many tools can confuse the model
   await agent.toolset(ToolSet1("t1"))
   await agent.toolset(ToolSet2("t2"))
   await agent.toolset(ToolSet3("t3"))
   # ...
