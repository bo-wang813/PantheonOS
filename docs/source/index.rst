.. Pantheon Agents documentation master file

Welcome to Pantheon Agents
==========================

.. image:: https://img.shields.io/badge/python-3.8+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License

**Pantheon Agents** is a distributed, multi-agent collaboration framework that enables AI agents with various toolsets to work together across different machines. Built for scalability and flexibility, it provides a robust foundation for creating complex multi-agent systems.

.. grid:: 1 1 2 2
   :gutter: 2

   .. grid-item-card:: 🚀 Quick Start
      :link: quickstart
      :link-type: doc

      Get up and running with Pantheon Agents in minutes. Learn the basics and create your first agent team.

   .. grid-item-card:: 📖 User Guide
      :link: guides/index
      :link-type: doc

      Comprehensive guides covering all aspects of the framework, from basic concepts to advanced features.

   .. grid-item-card:: 🔧 API Reference
      :link: api/index
      :link-type: doc

      Complete API documentation with detailed descriptions of all classes, methods, and functions.

   .. grid-item-card:: 💡 Examples
      :link: examples/index
      :link-type: doc

      Practical examples and tutorials demonstrating real-world use cases and best practices.

Key Features
------------

.. grid:: 1 2 2 3
   :gutter: 3

   .. grid-item::

      **🤖 Distributed Agents**
      
      Deploy agents across multiple machines with seamless communication and coordination.

   .. grid-item::

      **🛠️ Extensible Toolsets**
      
      Rich set of built-in tools (Python, R, Shell, Web, Files) with easy extension support.

   .. grid-item::

      **🧠 Persistent Memory**
      
      File-based memory system for maintaining agent state and context across sessions.

   .. grid-item::

      **👥 Team Collaboration**
      
      Multiple collaboration patterns: Sequential, Swarm, SwarmCenter, and Mixture of Agents (MoA).

   .. grid-item::

      **💬 ChatRoom Service**
      
      Host agent interactions with built-in conversation management and history tracking.

   .. grid-item::

      **🔌 Easy Integration**
      
      Simple API for integrating with existing systems and creating custom agent behaviors.

Architecture Overview
--------------------

.. code-block:: text

   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │   Agent A   │     │   Agent B   │     │   Agent C   │
   │  (Machine 1)│     │  (Machine 2)│     │  (Machine 3)│
   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
          │                    │                    │
          └────────────────────┴────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Team Manager    │
                    │  (Coordination)   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  ChatRoom Service │
                    │  (Conversation)   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Memory System    │
                    │  (Persistence)    │
                    └───────────────────┘

Quick Example
-------------

.. code-block:: python

   from pantheon import Agent, Team
   from pantheon.tools import PythonTools, WebTools

   # Create agents with different capabilities
   coder = Agent(
       name="Coder",
       instructions="You are an expert Python developer",
       tools=[PythonTools()]
   )

   researcher = Agent(
       name="Researcher", 
       instructions="You research information from the web",
       tools=[WebTools()]
   )

   # Create a team with Sequential collaboration
   team = Team(
       agents=[researcher, coder],
       pattern="sequential"
   )

   # Execute a task
   result = await team.execute(
       "Research the latest AI trends and create a summary script"
   )

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart
   concepts

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: User Guide

   guides/index
   guides/agents
   guides/teams
   guides/tools
   guides/memory
   guides/chatroom
   guides/distributed

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: API Reference

   api/index
   api/agent
   api/team
   api/tools
   api/memory
   api/chatroom

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Examples & Tutorials

   examples/index
   examples/basic_agent
   examples/team_collaboration
   examples/custom_tools
   examples/distributed_setup

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Development

   contributing
   changelog
   license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`