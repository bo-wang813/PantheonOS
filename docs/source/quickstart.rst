Quick Start
===========

This guide will help you create your first Pantheon agent and team in just a few minutes.

.. note::
   
   Make sure you have completed the :doc:`installation` before proceeding.

Your First Agent
----------------

Let's create a simple agent that can help with Python programming:

.. code-block:: python

   from pantheon import Agent
   from pantheon.tools import PythonTools

   # Create an agent with Python capabilities
   coder = Agent(
       name="PythonExpert",
       instructions="""You are an expert Python developer. 
       Help users write clean, efficient Python code.""",
       tools=[PythonTools()]
   )

   # Execute a task
   response = await coder.execute(
       "Write a function to calculate fibonacci numbers"
   )
   print(response)

Working with Tools
------------------

Agents become powerful when equipped with tools. Here's an example with multiple tools:

.. code-block:: python

   from pantheon import Agent
   from pantheon.tools import PythonTools, ShellTools, FileTools

   # Create a versatile agent
   assistant = Agent(
       name="DevAssistant",
       instructions="You help with development tasks",
       tools=[
           PythonTools(),
           ShellTools(allowed_commands=["ls", "grep", "find"]),
           FileTools(allowed_paths=["./workspace"])
       ]
   )

   # Complex task involving multiple tools
   result = await assistant.execute("""
   1. List all Python files in the current directory
   2. Find files containing 'TODO' comments
   3. Create a summary report
   """)

Creating a Team
---------------

Teams enable multiple agents to collaborate:

Sequential Team
~~~~~~~~~~~~~~~

Agents work one after another, passing results forward:

.. code-block:: python

   from pantheon import Team
   from pantheon.tools import WebTools, PythonTools

   # Create specialized agents
   researcher = Agent(
       name="Researcher",
       instructions="Research topics using web search",
       tools=[WebTools()]
   )

   analyst = Agent(
       name="Analyst",
       instructions="Analyze data and create visualizations",
       tools=[PythonTools()]
   )

   # Create a sequential team
   team = Team(
       agents=[researcher, analyst],
       pattern="sequential"
   )

   # Execute team task
   result = await team.execute(
       "Research Python trends and create a visualization"
   )

Swarm Team
~~~~~~~~~~

Agents work in parallel and coordinate dynamically:

.. code-block:: python

   # Create a swarm team for collaborative problem-solving
   swarm = Team(
       agents=[
           Agent(name="Planner", instructions="Create project plans"),
           Agent(name="Coder", instructions="Write code", tools=[PythonTools()]),
           Agent(name="Tester", instructions="Test and validate code")
       ],
       pattern="swarm"
   )

   result = await swarm.execute(
       "Create a web scraping tool with tests"
   )

Using Memory
------------

Enable persistent memory for context retention:

.. code-block:: python

   from pantheon import Agent
   from pantheon.memory import FileMemory

   # Create agent with memory
   agent = Agent(
       name="MemoryBot",
       instructions="Remember user preferences and past conversations",
       memory=FileMemory(path="./agent_memory")
   )

   # First interaction
   await agent.execute("My favorite color is blue")

   # Later interaction (remembers context)
   response = await agent.execute("What's my favorite color?")
   # Output: "Your favorite color is blue"

ChatRoom Service
----------------

For interactive conversations, use the ChatRoom service:

.. code-block:: python

   from pantheon.chatroom import ChatRoom
   from pantheon import Agent

   # Create a chatroom with agents
   chatroom = ChatRoom(
       name="DevHelper",
       agents=[
           Agent(name="Coder", tools=[PythonTools()]),
           Agent(name="Reviewer", instructions="Review code quality")
       ]
   )

   # Start the service
   await chatroom.start(port=8000)

   # Interact via API
   # POST http://localhost:8000/chat
   # {"message": "Help me write a REST API"}

Complete Example
----------------

Here's a complete example combining multiple concepts:

.. code-block:: python

   import asyncio
   from pantheon import Agent, Team
   from pantheon.tools import PythonTools, WebTools, FileTools
   from pantheon.memory import FileMemory

   async def main():
       # Create specialized agents with memory
       researcher = Agent(
           name="WebResearcher",
           instructions="Research technical topics thoroughly",
           tools=[WebTools()],
           memory=FileMemory(path="./memory/researcher")
       )
       
       developer = Agent(
           name="Developer",
           instructions="Write high-quality Python code with tests",
           tools=[PythonTools(), FileTools()],
           memory=FileMemory(path="./memory/developer")
       )
       
       # Create a team
       team = Team(
           agents=[researcher, developer],
           pattern="sequential",
           name="ResearchAndDevelop"
       )
       
       # Execute a complex task
       result = await team.execute("""
       Research best practices for Python async programming and 
       create a demonstration script showing proper usage of 
       asyncio with error handling and performance optimization.
       """)
       
       print(result)

   # Run the example
   if __name__ == "__main__":
       asyncio.run(main())

Running the Examples
--------------------

Save any example to a file (e.g., ``example.py``) and run:

.. code-block:: bash

   # Make sure environment is activated
   conda activate pantheon

   # Set API key
   export OPENAI_API_KEY="your-key"

   # Run the example
   python example.py

What's Next?
------------

Now that you've created your first agents and teams:

- Explore :doc:`concepts` to understand the framework better
- Check :doc:`guides/agents` for advanced agent configuration
- Learn about :doc:`guides/teams` for complex collaboration patterns
- Create :doc:`guides/tools` to extend agent capabilities
- Set up :doc:`guides/distributed` for multi-machine deployments

Tips for Success
----------------

.. tip::

   **Start Simple**: Begin with single agents before moving to teams.

.. tip::

   **Use Clear Instructions**: Well-written agent instructions lead to better results.

.. tip::

   **Choose Tools Wisely**: Only give agents the tools they need for their role.

.. tip::

   **Test Incrementally**: Test each agent individually before combining them.

.. warning::

   **API Costs**: Be mindful of API usage, especially with large teams or long-running tasks.