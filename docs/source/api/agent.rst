Agent API
=========

.. module:: pantheon.agent

The Agent class is the core building block of the Pantheon framework.

Agent Class
-----------

.. autoclass:: pantheon.Agent
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from pantheon import Agent
   
   # Create a simple agent
   agent = Agent(
       name="Assistant",
       instructions="You are a helpful assistant"
   )
   
   # Execute a task
   response = await agent.execute("Hello!")

Constructor Parameters
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - name
     - str
     - Unique identifier for the agent
   * - instructions
     - str
     - Natural language instructions defining agent behavior
   * - tools
     - List[Tool]
     - Optional list of tools available to the agent
   * - memory
     - Memory
     - Optional memory system for persistence
   * - model
     - str
     - LLM model to use (default: "gpt-4")
   * - temperature
     - float
     - Sampling temperature (0.0-2.0, default: 0.7)
   * - max_tokens
     - int
     - Maximum response tokens (default: 2000)

Methods
~~~~~~~

.. method:: execute(task: str, context: Dict[str, Any] = None) -> AgentResponse

   Execute a task with optional context.

   :param task: The task description or prompt
   :param context: Optional context dictionary
   :return: AgentResponse object containing the result

.. method:: initialize() -> None

   Initialize the agent and its resources.

.. method:: cleanup() -> None

   Clean up agent resources.

.. method:: save_state() -> Dict[str, Any]

   Save the current agent state.

.. method:: from_state(state: Dict[str, Any]) -> Agent

   Create an agent from saved state.

Properties
~~~~~~~~~~

.. attribute:: name

   The agent's unique identifier.

.. attribute:: tools

   List of available tools.

.. attribute:: memory

   The agent's memory system.

.. attribute:: metrics

   Performance metrics for the agent.

AgentResponse Class
-------------------

.. autoclass:: pantheon.AgentResponse
   :members:
   :undoc-members:

Response Attributes
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - Attribute
     - Type
     - Description
   * - content
     - str
     - The main response content
   * - success
     - bool
     - Whether the task completed successfully
   * - metadata
     - Dict
     - Additional response metadata
   * - tool_calls
     - List[ToolCall]
     - Tools used during execution
   * - tokens_used
     - int
     - Total tokens consumed

AgentError Class
----------------

.. autoclass:: pantheon.AgentError
   :members:
   :show-inheritance:

Error Types
~~~~~~~~~~~

- ``initialization_error``: Agent initialization failed
- ``execution_error``: Task execution failed
- ``tool_error``: Tool execution failed
- ``memory_error``: Memory operation failed
- ``timeout_error``: Operation timed out

Configuration Classes
---------------------

AgentConfig
~~~~~~~~~~~

.. autoclass:: pantheon.AgentConfig
   :members:
   :undoc-members:

Example configuration:

.. code-block:: python

   from pantheon import AgentConfig
   
   config = AgentConfig(
       model="gpt-4",
       temperature=0.7,
       max_tokens=2000,
       timeout=300,
       retry_policy={
           "max_attempts": 3,
           "backoff": "exponential"
       }
   )
   
   agent = Agent.from_config(config)

Helper Functions
----------------

.. autofunction:: pantheon.create_agent

.. autofunction:: pantheon.load_agent

.. autofunction:: pantheon.validate_agent_config

Events and Callbacks
--------------------

Agents emit events during their lifecycle:

.. code-block:: python

   from pantheon import Agent, AgentEvent
   
   async def on_task_start(event: AgentEvent):
       print(f"Starting task: {event.task}")
   
   async def on_task_complete(event: AgentEvent):
       print(f"Completed task: {event.result}")
   
   agent = Agent(
       name="EventAgent",
       callbacks={
           "on_task_start": on_task_start,
           "on_task_complete": on_task_complete
       }
   )

Available Events
~~~~~~~~~~~~~~~~

- ``on_initialize``: Agent initialization
- ``on_task_start``: Task execution begins
- ``on_tool_call``: Tool is invoked
- ``on_task_complete``: Task execution completes
- ``on_error``: Error occurs
- ``on_cleanup``: Agent cleanup

Advanced Features
-----------------

Streaming Responses
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async for chunk in agent.stream_execute("Generate a long story"):
       print(chunk, end="", flush=True)

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   tasks = ["Task 1", "Task 2", "Task 3"]
   results = await agent.batch_execute(tasks, max_concurrent=2)

Context Management
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   async with agent.context(user="alice", session="123"):
       response = await agent.execute("Hello")
       # Context automatically included

See Also
--------

- :doc:`team` - Team coordination with multiple agents
- :doc:`tools` - Available tools for agents
- :doc:`memory` - Memory systems for agents
- :doc:`../guides/agents` - Comprehensive agents guide