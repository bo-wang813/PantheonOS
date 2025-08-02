Core Concepts
=============

Understanding the core concepts of Pantheon Agents will help you build effective multi-agent systems.

Agents
------

An **Agent** is the fundamental building block of the Pantheon framework. Each agent is an autonomous entity with:

- **Identity**: A unique name and role
- **Instructions**: Natural language guidelines defining behavior
- **Tools**: Capabilities for interacting with the environment
- **Memory**: Optional persistent state storage
- **Model**: The LLM backend (OpenAI, Anthropic, etc.)

.. code-block:: python

   from pantheon import Agent
   from pantheon.tools import PythonTools

   agent = Agent(
       name="DataAnalyst",
       instructions="""You are a data analysis expert. 
       Analyze data, create visualizations, and provide insights.""",
       tools=[PythonTools()],
       model="gpt-4"
   )

Agent Lifecycle
~~~~~~~~~~~~~~~

.. mermaid::

   graph LR
       A[Initialize] --> B[Receive Task]
       B --> C[Process with LLM]
       C --> D[Execute Tools]
       D --> E[Update Memory]
       E --> F[Return Response]
       F --> B

Teams
-----

A **Team** is a collection of agents working together. Teams define:

- **Collaboration Pattern**: How agents coordinate
- **Communication Flow**: How information passes between agents
- **Task Distribution**: How work is divided

Collaboration Patterns
~~~~~~~~~~~~~~~~~~~~~~

**Sequential**
   Agents work in a defined order, each building on the previous agent's output.

   .. code-block:: text

      Agent A → Agent B → Agent C → Result

**Swarm**
   Agents work in parallel with dynamic coordination.

   .. code-block:: text

      ┌─→ Agent A ─┐
      │            ↓
      Task ─→ Agent B ─→ Result
      │            ↑
      └─→ Agent C ─┘

**SwarmCenter**
   A central coordinator manages multiple worker agents.

   .. code-block:: text

           ┌─→ Worker A
           │
      Center ─→ Worker B
           │
           └─→ Worker C

**Mixture of Agents (MoA)**
   Multiple agents propose solutions, then synthesize the best approach.

   .. code-block:: text

      ┌─→ Expert A ─┐
      │             │
      Task → Expert B → Synthesizer → Result
      │             │
      └─→ Expert C ─┘

Tools
-----

**Tools** extend agent capabilities beyond language processing:

Built-in Tools
~~~~~~~~~~~~~~

- **PythonTools**: Execute Python code in isolated environments
- **RTools**: Run R scripts for statistical analysis
- **ShellTools**: Execute shell commands with safety restrictions
- **WebTools**: Search and fetch web content
- **FileTools**: Read, write, and manipulate files
- **DatabaseTools**: Query and modify databases

Tool Safety
~~~~~~~~~~~

Tools include safety mechanisms:

.. code-block:: python

   from pantheon.tools import ShellTools

   # Restricted shell access
   safe_shell = ShellTools(
       allowed_commands=["ls", "grep", "cat"],
       forbidden_paths=["/etc", "/sys"],
       timeout=30  # seconds
   )

Custom Tools
~~~~~~~~~~~~

Create custom tools by extending the base class:

.. code-block:: python

   from pantheon.tools import Tool

   class WeatherTool(Tool):
       name = "weather"
       description = "Get weather information"
       
       async def execute(self, location: str) -> str:
           # Implementation here
           return f"Weather in {location}: Sunny, 72°F"

Memory
------

**Memory** provides persistent context across agent interactions:

Memory Types
~~~~~~~~~~~~

**FileMemory**
   Simple file-based storage for conversation history and state.

**VectorMemory**
   Semantic search over past interactions using embeddings.

**SQLiteMemory**
   Structured storage with query capabilities.

Memory Usage
~~~~~~~~~~~~

.. code-block:: python

   from pantheon.memory import FileMemory

   memory = FileMemory(
       path="./agent_memory",
       max_history=100,  # Keep last 100 interactions
       compression=True  # Compress old entries
   )

   agent = Agent(
       name="Assistant",
       memory=memory
   )

ChatRoom
--------

A **ChatRoom** is a service layer that:

- Hosts agent conversations
- Manages session state
- Provides REST API access
- Handles concurrent requests
- Maintains conversation history

.. code-block:: python

   from pantheon.chatroom import ChatRoom

   chatroom = ChatRoom(
       name="Support",
       agents=[agent1, agent2],
       max_concurrent_sessions=10,
       session_timeout=3600  # 1 hour
   )

Distributed Architecture
------------------------

Pantheon supports distributed deployment where agents run on different machines:

Remote Agents
~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.remote import RemoteAgent

   # Connect to agent on another machine
   remote_agent = RemoteAgent(
       name="GPUProcessor",
       host="gpu-server.local",
       port=8001,
       auth_token="secret"
   )

Communication Protocol
~~~~~~~~~~~~~~~~~~~~~~

Agents communicate using:

- **gRPC**: For high-performance RPC
- **REST**: For simple HTTP-based communication
- **Message Queue**: For asynchronous task distribution

Messages and Events
-------------------

Agent communication follows an event-driven model:

Message Types
~~~~~~~~~~~~~

- **TaskMessage**: New task assignment
- **ResponseMessage**: Task completion result
- **ErrorMessage**: Error or exception details
- **StatusMessage**: Progress updates
- **ControlMessage**: System commands

.. code-block:: python

   from pantheon.messages import TaskMessage

   message = TaskMessage(
       content="Analyze this dataset",
       sender="Coordinator",
       recipient="DataAnalyst",
       priority="high",
       metadata={"timeout": 300}
   )

Configuration
-------------

Pantheon uses hierarchical configuration:

1. **Default Config**: Built-in defaults
2. **System Config**: ``/etc/pantheon/config.yaml``
3. **User Config**: ``~/.pantheon/config.yaml``
4. **Project Config**: ``./pantheon.yaml``
5. **Environment Variables**: ``PANTHEON_*``
6. **Runtime Parameters**: Direct arguments

.. code-block:: yaml

   # pantheon.yaml
   agents:
     default:
       model: gpt-4
       temperature: 0.7
       max_tokens: 2000
   
   teams:
     timeout: 600
     max_retries: 3
   
   tools:
     python:
       sandbox: true
       packages:
         - numpy
         - pandas
         - matplotlib

Error Handling
--------------

Pantheon implements multi-level error handling:

Agent Level
~~~~~~~~~~~

.. code-block:: python

   agent = Agent(
       name="SafeAgent",
       error_handler=lambda e: f"Error occurred: {e}",
       retry_policy={"max_attempts": 3, "backoff": "exponential"}
   )

Team Level
~~~~~~~~~~

.. code-block:: python

   team = Team(
       agents=[agent1, agent2],
       on_agent_error="continue",  # or "halt", "replace"
       fallback_agent=backup_agent
   )

Best Practices
--------------

Agent Design
~~~~~~~~~~~~

1. **Single Responsibility**: Each agent should have one clear purpose
2. **Clear Instructions**: Use specific, actionable language
3. **Appropriate Tools**: Only provide necessary tools
4. **Error Handling**: Always handle potential failures

Team Composition
~~~~~~~~~~~~~~~~

1. **Complementary Skills**: Agents should have different strengths
2. **Clear Workflow**: Define how agents interact
3. **Scalability**: Design for varying workloads
4. **Monitoring**: Track team performance

Security Considerations
-----------------------

1. **Tool Restrictions**: Limit tool access appropriately
2. **API Key Management**: Use environment variables
3. **Network Security**: Use TLS for remote agents
4. **Input Validation**: Sanitize user inputs
5. **Output Filtering**: Check agent outputs

Performance Optimization
------------------------

1. **Caching**: Use memory to avoid repeated work
2. **Parallel Execution**: Use swarm patterns when possible
3. **Resource Limits**: Set timeouts and token limits
4. **Model Selection**: Choose appropriate model sizes
5. **Batch Processing**: Group similar tasks

Next Steps
----------

With these concepts understood, explore:

- :doc:`guides/agents` - Advanced agent configuration
- :doc:`guides/teams` - Team patterns in detail
- :doc:`guides/tools` - Creating custom tools
- :doc:`guides/distributed` - Distributed deployments