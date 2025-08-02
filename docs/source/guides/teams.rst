Teams Guide
===========

Teams in Pantheon enable multiple agents to collaborate on complex tasks. This guide covers team patterns, configuration, and best practices.

Team Fundamentals
-----------------

A team consists of:

- **Agents**: Individual AI entities with specific roles
- **Pattern**: The collaboration strategy
- **Coordinator**: Manages agent interactions
- **Communication**: How agents share information

Basic Team Creation
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import Agent, Team
   from pantheon.tools import PythonTools, WebTools

   # Create specialized agents
   researcher = Agent(
       name="Researcher",
       instructions="Research topics using web search",
       tools=[WebTools()]
   )

   analyst = Agent(
       name="Analyst",
       instructions="Analyze data and create insights",
       tools=[PythonTools()]
   )

   # Create a team
   team = Team(
       agents=[researcher, analyst],
       pattern="sequential",
       name="ResearchTeam"
   )

   # Execute team task
   result = await team.execute(
       "Research Python market trends and analyze the data"
   )

Collaboration Patterns
----------------------

Sequential Pattern
~~~~~~~~~~~~~~~~~~

Agents work in a defined order, each building on previous outputs.

**Use Cases**:
- Research → Analysis → Report
- Design → Implementation → Testing
- Data Collection → Processing → Visualization

.. code-block:: python

   from pantheon import Team

   # Create a sequential pipeline
   pipeline = Team(
       agents=[
           data_collector,
           data_cleaner,
           data_analyzer,
           report_generator
       ],
       pattern="sequential"
   )

   # Each agent receives the previous agent's output
   result = await pipeline.execute("Process sales data")

**Configuration Options**:

.. code-block:: python

   sequential_team = Team(
       agents=[agent1, agent2, agent3],
       pattern="sequential",
       config={
           "pass_full_history": True,  # Pass all previous outputs
           "allow_skip": True,  # Skip agents based on conditions
           "timeout_per_agent": 300,  # 5 minutes per agent
           "retry_failed_agents": True
       }
   )

Swarm Pattern
~~~~~~~~~~~~~

Agents work in parallel with dynamic coordination.

**Use Cases**:
- Parallel research on multiple topics
- Distributed problem solving
- Creative brainstorming

.. code-block:: python

   # Create a swarm for parallel processing
   swarm = Team(
       agents=[
           Agent(name="Researcher1", tools=[WebTools()]),
           Agent(name="Researcher2", tools=[WebTools()]),
           Agent(name="Researcher3", tools=[WebTools()])
       ],
       pattern="swarm"
   )

   # Agents work simultaneously
   result = await swarm.execute(
       "Research AI, blockchain, and quantum computing trends"
   )

**Swarm Configuration**:

.. code-block:: python

   swarm_team = Team(
       agents=agents,
       pattern="swarm",
       config={
           "coordination_method": "emergent",  # or "directed"
           "communication_rounds": 3,
           "consensus_threshold": 0.8,
           "max_parallel_agents": 5
       }
   )

SwarmCenter Pattern
~~~~~~~~~~~~~~~~~~~

A central coordinator manages distributed worker agents.

**Use Cases**:
- Task distribution systems
- Quality control workflows
- Hierarchical organizations

.. code-block:: python

   # Create center-coordinated team
   center_team = Team(
       agents=[
           coordinator,  # First agent is the center
           worker1,
           worker2,
           worker3
       ],
       pattern="swarmcenter"
   )

   # Center distributes and aggregates work
   result = await center_team.execute(
       "Analyze customer feedback across all channels"
   )

**Center Configuration**:

.. code-block:: python

   center_config = {
       "distribution_strategy": "load_balanced",  # or "round_robin", "capability_based"
       "aggregation_method": "synthesis",  # or "voting", "best_result"
       "worker_timeout": 180,
       "require_all_workers": False
   }

Mixture of Agents (MoA)
~~~~~~~~~~~~~~~~~~~~~~~

Multiple agents propose solutions, then synthesize the best approach.

**Use Cases**:
- Complex decision making
- Creative problem solving
- Consensus building

.. code-block:: python

   # Create MoA team
   moa_team = Team(
       agents=[
           expert1,
           expert2,
           expert3,
           synthesizer  # Last agent synthesizes
       ],
       pattern="moa"
   )

   # Experts propose, synthesizer combines
   result = await moa_team.execute(
       "Design a scalable microservices architecture"
   )

**MoA Configuration**:

.. code-block:: python

   moa_config = {
       "proposal_method": "independent",  # or "iterative"
       "synthesis_strategy": "best_of",  # or "combine_all", "weighted"
       "quality_threshold": 0.7,
       "require_consensus": False
   }

Advanced Team Configuration
---------------------------

Team Initialization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import Team
   from pantheon.coordinators import CustomCoordinator

   team = Team(
       agents=agents,
       pattern="sequential",
       name="AdvancedTeam",
       
       # Coordination
       coordinator=CustomCoordinator(),
       
       # Communication
       communication_protocol="structured",  # or "natural", "hybrid"
       
       # Memory
       shared_memory=TeamMemory(path="./team_memory"),
       
       # Error handling
       error_strategy="continue_on_error",  # or "halt_on_error", "retry"
       
       # Performance
       max_concurrent_executions=3,
       timeout=3600,  # 1 hour
       
       # Monitoring
       enable_metrics=True,
       log_level="INFO"
   )

Dynamic Team Composition
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import DynamicTeam

   # Team that adjusts based on task
   dynamic_team = DynamicTeam(
       agent_pool=[
           coder, tester, reviewer,
           designer, architect, devops
       ],
       selection_strategy="task_based"
   )

   # Team composition chosen per task
   result = await dynamic_team.execute(
       "Create a REST API with tests and deployment"
   )

Team Communication
------------------

Message Passing
~~~~~~~~~~~~~~~

.. code-block:: python

   # Configure how agents communicate
   team = Team(
       agents=agents,
       communication={
           "protocol": "structured",
           "format": "json",
           "include_metadata": True,
           "message_history_limit": 50
       }
   )

Shared Context
~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.memory import SharedContext

   # Shared context for all agents
   context = SharedContext(
       initial_state={"project": "webapp", "stage": "development"}
   )

   team = Team(
       agents=agents,
       shared_context=context
   )

Inter-Agent Messaging
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable direct agent communication
   team = Team(
       agents=agents,
       config={
           "enable_direct_messaging": True,
           "message_queue_size": 100,
           "message_ttl": 300  # 5 minutes
       }
   )

Team Patterns and Strategies
----------------------------

Pipeline Pattern
~~~~~~~~~~~~~~~~

Sequential processing with transformations:

.. code-block:: python

   # Data processing pipeline
   etl_pipeline = Team(
       agents=[
           Agent(name="Extractor", tools=[DatabaseTools()]),
           Agent(name="Transformer", tools=[PythonTools()]),
           Agent(name="Loader", tools=[DatabaseTools()])
       ],
       pattern="sequential",
       config={"pipeline_mode": True}
   )

Map-Reduce Pattern
~~~~~~~~~~~~~~~~~~

Parallel processing with aggregation:

.. code-block:: python

   # Map-reduce for distributed analysis
   mapreduce_team = Team(
       agents=[
           coordinator,
           *[Agent(f"Mapper{i}") for i in range(4)],
           reducer
       ],
       pattern="swarmcenter",
       config={
           "operation": "mapreduce",
           "partition_strategy": "hash"
       }
   )

Hierarchical Pattern
~~~~~~~~~~~~~~~~~~~~

Multi-level team structure:

.. code-block:: python

   # Hierarchical organization
   org_team = Team(
       agents=[ceo],
       sub_teams=[
           Team("Engineering", [cto, developers]),
           Team("Marketing", [cmo, marketers]),
           Team("Sales", [cso, sales_reps])
       ],
       pattern="hierarchical"
   )

Error Handling and Recovery
---------------------------

Team-Level Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def team_error_handler(error, agent, task):
       if isinstance(error, TimeoutError):
           return {"action": "retry", "delay": 60}
       elif isinstance(error, AgentError):
           return {"action": "skip", "fallback": default_response}
       else:
           return {"action": "halt"}

   team = Team(
       agents=agents,
       error_handler=team_error_handler
   )

Fault Tolerance
~~~~~~~~~~~~~~~

.. code-block:: python

   # Resilient team configuration
   resilient_team = Team(
       agents=agents,
       config={
           "retry_policy": {
               "max_retries": 3,
               "backoff": "exponential",
               "retry_on": [TimeoutError, ConnectionError]
           },
           "fallback_agents": {
               "Analyst": "BackupAnalyst",
               "Coder": "BackupCoder"
           },
           "health_check_interval": 60,
           "circuit_breaker": {
               "threshold": 5,
               "timeout": 300
           }
       }
   )

Performance Optimization
------------------------

Caching and Memoization
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.cache import TeamCache

   # Team-level caching
   team = Team(
       agents=agents,
       cache=TeamCache(
           strategy="lru",
           max_size=1000,
           ttl=3600
       )
   )

Parallel Execution
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Optimize parallel execution
   parallel_team = Team(
       agents=agents,
       pattern="swarm",
       config={
           "executor": "thread",  # or "process", "async"
           "max_workers": 10,
           "batch_size": 5,
           "queue_size": 100
       }
   )

Resource Management
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Control resource usage
   team = Team(
       agents=agents,
       resource_limits={
           "max_total_memory": "4GB",
           "max_total_cpu": 8,
           "max_concurrent_tools": 10,
           "rate_limits": {
               "api_calls": "100/minute",
               "tokens": "1000000/hour"
           }
       }
   )

Monitoring and Observability
----------------------------

Team Metrics
~~~~~~~~~~~~

.. code-block:: python

   from pantheon.metrics import TeamMetrics

   metrics = TeamMetrics()
   team = Team(
       agents=agents,
       metrics=metrics
   )

   # Access metrics
   print(f"Total tasks: {metrics.total_tasks}")
   print(f"Success rate: {metrics.success_rate}")
   print(f"Avg completion time: {metrics.avg_completion_time}")
   print(f"Agent utilization: {metrics.agent_utilization}")

Distributed Tracing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.tracing import DistributedTracer

   tracer = DistributedTracer(
       service_name="pantheon-team",
       export_to="jaeger"
   )

   team = Team(
       agents=agents,
       tracer=tracer
   )

Real-World Examples
-------------------

Software Development Team
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Complete software development team
   dev_team = Team(
       agents=[
           Agent("ProductManager", instructions="Define requirements"),
           Agent("Architect", instructions="Design system architecture"),
           Agent("Developer", tools=[PythonTools()]),
           Agent("Tester", tools=[TestingTools()]),
           Agent("Reviewer", instructions="Review code quality")
       ],
       pattern="sequential",
       config={
           "checkpoints": True,  # Save progress
           "rollback_on_failure": True
       }
   )

Research and Analysis Team
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Multi-source research team
   research_team = Team(
       agents=[
           Agent("WebResearcher", tools=[WebTools()]),
           Agent("DataAnalyst", tools=[PythonTools()]),
           Agent("Visualizer", tools=[VisualizationTools()]),
           Agent("ReportWriter", tools=[DocumentTools()])
       ],
       pattern="sequential"
   )

Customer Support Team
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Hierarchical support team
   support_team = Team(
       agents=[
           Agent("Dispatcher", instructions="Route queries"),
           Agent("TechSupport", tools=[DatabaseTools()]),
           Agent("BillingSupport", tools=[BillingTools()]),
           Agent("Escalation", instructions="Handle complex cases")
       ],
       pattern="swarmcenter"
   )

Best Practices
--------------

1. **Clear Roles**: Define specific responsibilities for each agent
2. **Appropriate Patterns**: Choose patterns that match your workflow
3. **Error Planning**: Implement comprehensive error handling
4. **Performance Monitoring**: Track metrics and optimize
5. **Testing**: Test team configurations thoroughly
6. **Documentation**: Document team structures and workflows

Next Steps
----------

- Explore :doc:`tools` to enhance agent capabilities
- Learn about :doc:`memory` for team persistence
- Set up :doc:`distributed` for scaling teams
- Review :doc:`chatroom` for interactive team services