Basic Agent Example
===================

This example demonstrates how to create and use a basic Pantheon agent.

Objective
---------

Learn the fundamentals of creating agents, executing tasks, and handling responses.

Prerequisites
-------------

- Pantheon Agents installed
- OpenAI API key set in environment

Simple Agent
------------

The most basic agent requires only a name and instructions:

.. code-block:: python

   import asyncio
   from pantheon import Agent
   
   async def main():
       # Create a simple agent
       agent = Agent(
           name="Assistant",
           instructions="You are a helpful, friendly assistant."
       )
       
       # Execute a task
       response = await agent.execute("What is the capital of France?")
       print(response.content)
       # Output: The capital of France is Paris.
   
   if __name__ == "__main__":
       asyncio.run(main())

Agent with Tools
----------------

Add tools to give your agent additional capabilities:

.. code-block:: python

   import asyncio
   from pantheon import Agent
   from pantheon.tools import PythonTools, WebTools
   
   async def main():
       # Create an agent with tools
       agent = Agent(
           name="ResearchAssistant",
           instructions="""You are a research assistant.
           Use web search to find information and Python to analyze data.""",
           tools=[WebTools(), PythonTools()]
       )
       
       # Complex task using multiple tools
       response = await agent.execute("""
       Search for the current population of the top 5 most populous countries,
       then create a bar chart comparing them.
       """)
       
       print(response.content)
       # Agent will search the web and create a visualization
   
   if __name__ == "__main__":
       asyncio.run(main())

Agent with Memory
-----------------

Enable memory for context retention across interactions:

.. code-block:: python

   import asyncio
   from pantheon import Agent
   from pantheon.memory import FileMemory
   
   async def main():
       # Create memory system
       memory = FileMemory(path="./agent_memory")
       
       # Create agent with memory
       agent = Agent(
           name="PersonalAssistant",
           instructions="Remember user preferences and past conversations.",
           memory=memory
       )
       
       # First interaction
       response1 = await agent.execute("My name is Alice and I like Python.")
       print("Agent:", response1.content)
       
       # Second interaction (remembers context)
       response2 = await agent.execute("What's my name and what do I like?")
       print("Agent:", response2.content)
       # Output: Your name is Alice and you like Python.
   
   if __name__ == "__main__":
       asyncio.run(main())

Error Handling
--------------

Properly handle errors and edge cases:

.. code-block:: python

   import asyncio
   from pantheon import Agent, AgentError
   
   async def main():
       agent = Agent(
           name="SafeAgent",
           instructions="You help with calculations."
       )
       
       try:
           # Normal execution
           response = await agent.execute("What is 2 + 2?")
           print(f"Success: {response.content}")
           
       except AgentError as e:
           print(f"Agent error: {e.message}")
           print(f"Error type: {e.error_type}")
           
       except Exception as e:
           print(f"Unexpected error: {e}")
   
   if __name__ == "__main__":
       asyncio.run(main())

Streaming Responses
-------------------

For long responses, use streaming:

.. code-block:: python

   import asyncio
   from pantheon import Agent
   
   async def main():
       agent = Agent(
           name="StoryTeller",
           instructions="You are a creative story teller."
       )
       
       print("Generating story...")
       async for chunk in agent.stream_execute(
           "Tell me a short story about a robot learning to paint"
       ):
           print(chunk, end="", flush=True)
       print("\n\nStory complete!")
   
   if __name__ == "__main__":
       asyncio.run(main())

Configuration Options
---------------------

Fine-tune agent behavior with configuration:

.. code-block:: python

   import asyncio
   from pantheon import Agent
   
   async def main():
       # Precise, focused responses
       precise_agent = Agent(
           name="PreciseAgent",
           instructions="Provide exact, concise answers.",
           model="gpt-4",
           temperature=0.2,  # Low temperature for consistency
           max_tokens=500    # Limit response length
       )
       
       # Creative, expansive responses
       creative_agent = Agent(
           name="CreativeAgent",
           instructions="Be creative and think outside the box.",
           model="gpt-4",
           temperature=0.9,  # High temperature for creativity
           max_tokens=2000   # Allow longer responses
       )
       
       task = "Describe a sunset"
       
       print("Precise Agent:")
       precise_response = await precise_agent.execute(task)
       print(precise_response.content)
       
       print("\nCreative Agent:")
       creative_response = await creative_agent.execute(task)
       print(creative_response.content)
   
   if __name__ == "__main__":
       asyncio.run(main())

Complete Example
----------------

A comprehensive example combining multiple features:

.. code-block:: python

   import asyncio
   import logging
   from pantheon import Agent
   from pantheon.tools import PythonTools, FileTools
   from pantheon.memory import FileMemory
   
   # Set up logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   async def main():
       # Initialize components
       memory = FileMemory(path="./data_analyst_memory")
       
       # Create a data analyst agent
       analyst = Agent(
           name="DataAnalyst",
           instructions="""You are an expert data analyst.
           - Analyze data thoroughly
           - Create clear visualizations
           - Provide actionable insights
           - Remember previous analyses""",
           tools=[
               PythonTools(packages=["pandas", "matplotlib", "seaborn"]),
               FileTools(allowed_paths=["./data", "./output"])
           ],
           memory=memory,
           model="gpt-4",
           temperature=0.3
       )
       
       try:
           # Task 1: Load and analyze data
           logger.info("Starting data analysis task...")
           
           response = await analyst.execute("""
           Create a sample dataset of monthly sales data for 2023.
           Include columns: month, product_category, sales_amount, units_sold.
           Generate realistic data for 3 product categories.
           Save the data as 'sales_2023.csv' and create a summary visualization.
           """)
           
           print("Analysis Complete:")
           print(response.content)
           
           # Task 2: Follow-up analysis (uses memory)
           logger.info("Performing follow-up analysis...")
           
           followup = await analyst.execute("""
           Based on the sales data we just analyzed,
           identify the best performing product category and
           create a detailed monthly trend analysis for it.
           """)
           
           print("\nFollow-up Analysis:")
           print(followup.content)
           
           # Check metrics
           if hasattr(analyst, 'metrics'):
               print(f"\nPerformance Metrics:")
               print(f"Total tokens used: {analyst.metrics.total_tokens}")
               print(f"Execution time: {analyst.metrics.last_execution_time}s")
           
       except Exception as e:
           logger.error(f"Error during analysis: {e}")
           
       finally:
           # Clean up
           await analyst.cleanup()
           logger.info("Agent cleanup complete")
   
   if __name__ == "__main__":
       asyncio.run(main())

Running the Examples
--------------------

1. Save any example to a file (e.g., ``basic_agent.py``)
2. Ensure your API key is set:

   .. code-block:: bash
   
      export OPENAI_API_KEY="your-api-key"

3. Run the example:

   .. code-block:: bash
   
      python basic_agent.py

Key Takeaways
-------------

- Agents are created with a name and instructions
- Tools extend agent capabilities
- Memory enables context retention
- Error handling ensures robustness
- Configuration options control behavior
- Streaming supports long responses

Next Steps
----------

- Explore :doc:`team_collaboration` for multi-agent systems
- Learn about :doc:`custom_tools` to extend capabilities
- Check :doc:`../guides/agents` for advanced patterns