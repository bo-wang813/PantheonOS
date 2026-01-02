Creating Custom Teams
=====================

This guide explains how to create custom team types by extending the base ``Team`` class to implement specialized collaboration patterns.

Overview
--------

Custom teams allow you to:

* Define unique agent coordination strategies
* Implement domain-specific collaboration patterns
* Control message flow between agents
* Add custom logic for task distribution

Base Class
----------

All teams inherit from the ``Team`` base class:

.. code-block:: python

   from pantheon.team.base import Team
   from pantheon.agent import Agent, AgentInput

   class Team(ABC):
       def __init__(self, agents: list[Agent]):
           self.agents = {}  # Dict[name, agent]
           self.events_queue = asyncio.Queue()

       async def async_setup(self):
           """Optional setup before running."""
           pass

       async def run(self, msg: AgentInput, **kwargs):
           """Execute the team's collaboration pattern."""
           pass

       async def chat(self, message: str | dict | None = None):
           """Start interactive REPL session."""
           pass

Creating a Custom Team
----------------------

Basic Structure
~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.team.base import Team
   from pantheon.agent import Agent, AgentInput

   class MyCustomTeam(Team):
       def __init__(self, agents: list[Agent], my_param: str = "default"):
           super().__init__(agents)
           self.my_param = my_param

       async def run(self, msg: AgentInput, **kwargs):
           # Implement your collaboration logic
           pass

Example: Round-Robin Team
~~~~~~~~~~~~~~~~~~~~~~~~~

A team where agents take turns responding until a condition is met:

.. code-block:: python

   from pantheon.team.base import Team
   from pantheon.agent import Agent, AgentInput

   class RoundRobinTeam(Team):
       """Team where agents take turns responding."""

       def __init__(
           self,
           agents: list[Agent],
           max_rounds: int = 3,
       ):
           super().__init__(agents)
           self.agent_order = list(self.agents.keys())
           self.max_rounds = max_rounds

       async def run(self, msg: AgentInput, **kwargs):
           # Convert input to message history
           first_agent = self.agents[self.agent_order[0]]
           history = first_agent.input_to_openai_messages(msg, False)

           result = None
           for round_num in range(self.max_rounds):
               for agent_name in self.agent_order:
                   agent = self.agents[agent_name]

                   # Run agent with current history
                   result = await agent.run(history, **kwargs)

                   # Add agent's response to history
                   history.append({
                       "role": "assistant",
                       "content": f"[{agent_name}]: {result.content}"
                   })

                   # Check if task is complete
                   if self._is_complete(result):
                       return result

           return result

       def _is_complete(self, result) -> bool:
           """Override to define completion criteria."""
           return "COMPLETE" in result.content.upper()

Example: Voting Team
~~~~~~~~~~~~~~~~~~~~

A team where multiple agents vote on a decision:

.. code-block:: python

   from collections import Counter
   from pantheon.team.base import Team
   from pantheon.agent import Agent, AgentInput

   class VotingTeam(Team):
       """Team where agents vote on decisions."""

       def __init__(
           self,
           agents: list[Agent],
           vote_prompt: str = "Vote YES or NO:",
       ):
           super().__init__(agents)
           self.vote_prompt = vote_prompt

       async def run(self, msg: AgentInput, **kwargs):
           import asyncio

           # Create voting prompt
           first_agent = list(self.agents.values())[0]
           history = first_agent.input_to_openai_messages(msg, False)
           history.append({"role": "user", "content": self.vote_prompt})

           # Collect votes from all agents in parallel
           async def get_vote(agent):
               result = await agent.run(history, **kwargs)
               return self._parse_vote(result.content)

           tasks = [get_vote(agent) for agent in self.agents.values()]
           votes = await asyncio.gather(*tasks)

           # Tally votes
           vote_counts = Counter(votes)
           winner = vote_counts.most_common(1)[0]

           # Create result
           from pantheon.agent import AgentOutput
           return AgentOutput(
               content=f"Vote result: {winner[0]} ({winner[1]}/{len(votes)} votes)",
               details={"votes": dict(vote_counts)}
           )

       def _parse_vote(self, content: str) -> str:
           content_upper = content.upper()
           if "YES" in content_upper:
               return "YES"
           elif "NO" in content_upper:
               return "NO"
           return "ABSTAIN"

Example: Hierarchical Team
~~~~~~~~~~~~~~~~~~~~~~~~~~

A team with manager and worker agents:

.. code-block:: python

   from pantheon.team.base import Team
   from pantheon.agent import Agent, AgentInput

   class HierarchicalTeam(Team):
       """Team with a manager who delegates to workers."""

       def __init__(
           self,
           manager: Agent,
           workers: list[Agent],
       ):
           all_agents = [manager] + workers
           super().__init__(all_agents)
           self.manager = manager
           self.workers = {w.name: w for w in workers}

       async def async_setup(self):
           # Add delegation tool to manager
           @self.manager.tool
           async def delegate(worker_name: str, task: str) -> str:
               """Delegate a task to a worker agent.

               Args:
                   worker_name: Name of the worker to delegate to
                   task: The task description
               """
               if worker_name not in self.workers:
                   return f"Unknown worker: {worker_name}"

               worker = self.workers[worker_name]
               result = await worker.run(task)
               return f"[{worker_name}]: {result.content}"

           @self.manager.tool
           def list_workers() -> str:
               """List available worker agents."""
               return "\n".join([
                   f"- {name}: {w.instructions[:100]}..."
                   for name, w in self.workers.items()
               ])

       async def run(self, msg: AgentInput, **kwargs):
           # Manager handles the request, delegating as needed
           return await self.manager.run(msg, **kwargs)

Key Methods to Implement
------------------------

run()
~~~~~

The main entry point for team execution:

.. code-block:: python

   async def run(self, msg: AgentInput, **kwargs):
       """
       Execute the team's collaboration pattern.

       Args:
           msg: User input (str, dict, or list of messages)
           **kwargs: Additional arguments passed to agents

       Returns:
           AgentOutput: The final response from the team
       """
       # Your collaboration logic here
       pass

async_setup()
~~~~~~~~~~~~~

Optional initialization before first run:

.. code-block:: python

   async def async_setup(self):
       """Called once before the team starts processing."""
       # Register tools, initialize resources, etc.
       pass

gather_events()
~~~~~~~~~~~~~~~

For advanced event handling (streaming, progress updates):

.. code-block:: python

   async def gather_events(self):
       """Collect events from all agents into team's event queue."""
       async def _gather_agent_events(agent):
           while True:
               event = await agent.events_queue.get()
               self.events_queue.put_nowait({
                   "agent_name": agent.name,
                   "event": event,
               })

       tasks = [_gather_agent_events(a) for a in self.agents.values()]
       await asyncio.gather(*tasks)

Working with Messages
---------------------

Convert input to message history:

.. code-block:: python

   # Convert AgentInput to OpenAI message format
   agent = list(self.agents.values())[0]
   history = agent.input_to_openai_messages(msg, False)

   # Add messages to history
   history.append({"role": "user", "content": "Next step"})
   history.append({"role": "assistant", "content": response})

   # Pass history between agents
   result = await next_agent.run(history)
   history.extend(result.details.messages)

Best Practices
--------------

1. **Call super().__init__()**: Always initialize the base class with agents list
2. **Use agent names**: Access agents via ``self.agents[name]`` dictionary
3. **Handle errors gracefully**: Wrap agent calls in try/except for robustness
4. **Support streaming**: Use ``events_queue`` for real-time updates
5. **Document behavior**: Add clear docstrings explaining the collaboration pattern
6. **Test edge cases**: Handle scenarios with 1 agent, failed agents, etc.

Using Custom Teams
------------------

.. code-block:: python

   import asyncio
   from pantheon import Agent

   async def main():
       # Create agents
       agent1 = Agent(name="analyst", instructions="Analyze data.")
       agent2 = Agent(name="writer", instructions="Write reports.")
       agent3 = Agent(name="reviewer", instructions="Review content.")

       # Create custom team
       team = RoundRobinTeam(
           agents=[agent1, agent2, agent3],
           max_rounds=2
       )

       # Run task
       result = await team.run("Analyze Q4 sales data and write a report")
       print(result.content)

       # Or use interactive chat
       await team.chat()

   asyncio.run(main())
