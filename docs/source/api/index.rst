API Reference
=============

This section provides detailed API documentation for all Pantheon Agents modules, classes, and functions.

.. note::
   
   The API is designed to be intuitive and follows Python conventions. All async methods should be called with ``await``.

Core Modules
------------

.. grid:: 1 1 2 2
   :gutter: 3

   .. grid-item-card:: Agent
      :link: agent
      :link-type: doc

      Core Agent class and related functionality for creating autonomous AI agents.

   .. grid-item-card:: Team
      :link: team
      :link-type: doc

      Team coordination and collaboration patterns for multi-agent systems.

   .. grid-item-card:: Tools
      :link: tools
      :link-type: doc

      Built-in and custom tool implementations for extending agent capabilities.

   .. grid-item-card:: Memory
      :link: memory
      :link-type: doc

      Memory systems for persistent context and state management.

   .. grid-item-card:: ChatRoom
      :link: chatroom
      :link-type: doc

      Interactive service layer for hosting agent conversations.

   .. grid-item-card:: Remote
      :link: remote
      :link-type: doc

      Distributed agent support for multi-machine deployments.

Quick Reference
---------------

Common Imports
~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import Agent, Team
   from pantheon.tools import PythonTools, WebTools, FileTools
   from pantheon.memory import FileMemory, VectorMemory
   from pantheon.chatroom import ChatRoom
   from pantheon.remote import RemoteAgent

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   # Create an agent
   agent = Agent(
       name="Assistant",
       instructions="You are a helpful assistant",
       tools=[PythonTools()]
   )

   # Execute a task
   result = await agent.execute("Hello, how can you help?")

   # Create a team
   team = Team(
       agents=[agent1, agent2],
       pattern="sequential"
   )

   # Run team task
   team_result = await team.execute("Complex task")

Module Structure
----------------

.. code-block:: text

   pantheon/
   ├── __init__.py          # Main exports
   ├── agent.py             # Agent implementation
   ├── team.py              # Team coordination
   ├── memory.py            # Memory systems
   ├── tools/               # Tool implementations
   │   ├── __init__.py
   │   ├── python.py
   │   ├── web.py
   │   ├── file.py
   │   └── ...
   ├── chatroom/            # ChatRoom service
   │   ├── __init__.py
   │   ├── service.py
   │   └── ...
   └── remote/              # Distributed support
       ├── __init__.py
       ├── client.py
       └── server.py

.. toctree::
   :hidden:
   :maxdepth: 2

   agent
   team
   tools
   memory
   chatroom
   remote
   messages
   errors
   utils