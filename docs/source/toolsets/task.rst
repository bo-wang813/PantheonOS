TaskToolSet
===========

The TaskToolSet provides modal workflow management for structured agent execution, enabling task tracking, mode transitions, and user notifications with confidence scoring.

Overview
--------

Key features:

* **Task Boundaries**: Track task progress with mode transitions
* **Modal Workflow**: Support for PLANNING/EXECUTION/VERIFICATION or RESEARCH/ANALYSIS/INTERPRETATION modes
* **User Notifications**: Structured communication with confidence scoring
* **State Persistence**: Task state persisted to disk across sessions
* **Artifact Tracking**: Automatic detection of file modifications

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import TaskToolSet

   # Create task toolset
   task_tools = TaskToolSet(name="task")

   # Create agent and add toolset at runtime
   agent = Agent(
       name="developer",
       instructions="You manage tasks using structured workflows.",
       model="gpt-4o"
   )
   await agent.toolset(task_tools)

   await agent.chat()

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
     - Name of the toolset (default: "task")

Tools Reference
---------------

task_boundary
~~~~~~~~~~~~~

Indicate the start of a task or update the current task status. This tool should be called as the first tool in any tool call batch.

.. code-block:: python

   result = await task_tools.task_boundary(
       TaskName="Implementing Authentication",
       Mode="EXECUTION",
       TaskSummary="Set up project structure and created `auth.py` module",
       TaskStatus="Adding JWT token validation",
       PredictedTaskSize=15
   )

**Parameters:**

- ``TaskName``: Human-readable task identifier (e.g., "Researching Existing Server Implementation")
- ``Mode``: Agent focus mode - PLANNING/EXECUTION/VERIFICATION (coding) or RESEARCH/ANALYSIS/INTERPRETATION (research)
- ``TaskSummary``: Concise summary of accomplishments so far (1-2 lines, past tense)
- ``TaskStatus``: Active status describing what will happen next
- ``PredictedTaskSize``: Estimated number of tool calls to complete the task
- ``waitForPreviousTools``: If true, wait for previous tool calls to complete (default: False)

**Special Value:**

Use ``"%SAME%"`` for Mode, TaskName, TaskStatus, or TaskSummary to reuse the previous value.

.. code-block:: python

   # Update status only, keep same task name and mode
   result = await task_tools.task_boundary(
       TaskName="%SAME%",
       Mode="%SAME%",
       TaskSummary="Completed authentication module with tests",
       TaskStatus="Running final test suite",
       PredictedTaskSize=3
   )

**Returns:**

.. code-block:: python

   {"success": True, "mode": "EXECUTION", "task": "Implementing Authentication"}

notify_user
~~~~~~~~~~~

Communicate with the user during task execution. This is the primary way to send messages when working within a task boundary.

.. code-block:: python

   result = await task_tools.notify_user(
       PathsToReview=["src/auth.py", "tests/test_auth.py"],
       BlockedOnUser=True,
       Message="## Authentication Implementation Complete\n\nI've implemented JWT-based authentication. Please review the files.",
       ConfidenceJustification="(1) Gaps: No (2) Assumptions: No (3) Complexity: No (4) Risk: No (5) Ambiguity: No (6) Irreversible: No",
       ConfidenceScore=0.9
   )

**Parameters:**

- ``PathsToReview``: List of absolute file paths the user should review
- ``BlockedOnUser``: True if waiting for user approval, False if just notifying
- ``Message``: Notification message in GitHub Flavored Markdown format
- ``ConfidenceJustification``: Answers to the 6 confidence assessment questions (Yes/No)
- ``ConfidenceScore``: Confidence level from 0.0 to 1.0
- ``waitForPreviousTools``: Should be True to ensure sequential execution (default: True)

**Confidence Scoring Guide:**

Before setting ConfidenceScore, answer these 6 questions:

1. **Gaps** - Any missing parts?
2. **Assumptions** - Any unverified assumptions?
3. **Complexity** - Complex logic with unknowns?
4. **Risk** - Non-trivial interactions with bug risk?
5. **Ambiguity** - Unclear requirements forcing design choices?
6. **Irreversible** - Difficult to revert?

**Scoring:**

- **0.8-1.0**: "No" to ALL questions
- **0.5-0.7**: "Yes" to 1-2 questions
- **0.0-0.4**: "Yes" to 3+ questions

**Returns:**

.. code-block:: python

   {
       "success": True,
       "interrupt": True,
       "message": "## Authentication Implementation Complete...",
       "paths": ["src/auth.py", "tests/test_auth.py"]
   }

Workflow Modes
--------------

Coding Workflow
~~~~~~~~~~~~~~~

- **PLANNING**: Analyzing requirements, designing solutions
- **EXECUTION**: Writing code, implementing features
- **VERIFICATION**: Testing, reviewing, validating results

Research Workflow
~~~~~~~~~~~~~~~~~

- **RESEARCH**: Gathering information, exploring options
- **ANALYSIS**: Processing and interpreting findings
- **INTERPRETATION**: Drawing conclusions, summarizing insights

Examples
--------

Complete Coding Workflow
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Start planning phase
   await task_tools.task_boundary(
       TaskName="Add User Profile Feature",
       Mode="PLANNING",
       TaskSummary="Starting new feature implementation",
       TaskStatus="Analyzing existing user model",
       PredictedTaskSize=20
   )

   # Transition to execution
   await task_tools.task_boundary(
       TaskName="%SAME%",
       Mode="EXECUTION",
       TaskSummary="Designed database schema and API endpoints",
       TaskStatus="Creating user profile model",
       PredictedTaskSize=15
   )

   # ... implement feature ...

   # Verification phase
   await task_tools.task_boundary(
       TaskName="%SAME%",
       Mode="VERIFICATION",
       TaskSummary="Implemented profile model, API, and frontend",
       TaskStatus="Running integration tests",
       PredictedTaskSize=5
   )

   # Notify user for review
   await task_tools.notify_user(
       PathsToReview=[
           "src/models/profile.py",
           "src/api/profile.py",
           "tests/test_profile.py"
       ],
       BlockedOnUser=True,
       Message="## User Profile Feature Complete\n\nImplemented:\n- Profile model with avatar support\n- REST API endpoints\n- Integration tests\n\nPlease review before merge.",
       ConfidenceJustification="(1) No (2) No (3) No (4) Yes - new DB migrations (5) No (6) No",
       ConfidenceScore=0.75
   )

Research Workflow
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Research phase
   await task_tools.task_boundary(
       TaskName="Evaluate Authentication Libraries",
       Mode="RESEARCH",
       TaskSummary="Starting security library evaluation",
       TaskStatus="Surveying popular JWT libraries",
       PredictedTaskSize=10
   )

   # Analysis phase
   await task_tools.task_boundary(
       TaskName="%SAME%",
       Mode="ANALYSIS",
       TaskSummary="Identified 5 candidate libraries",
       TaskStatus="Comparing security features and performance",
       PredictedTaskSize=8
   )

   # Interpretation phase
   await task_tools.task_boundary(
       TaskName="%SAME%",
       Mode="INTERPRETATION",
       TaskSummary="Benchmarked all libraries, reviewed security advisories",
       TaskStatus="Preparing recommendation summary",
       PredictedTaskSize=3
   )

   # Notify with findings
   await task_tools.notify_user(
       PathsToReview=[],
       BlockedOnUser=False,
       Message="## Library Evaluation Complete\n\n**Recommendation:** PyJWT\n\n| Library | Security | Performance | Maintenance |\n|---------|----------|-------------|-------------|\n| PyJWT | ★★★★★ | ★★★★ | Active |\n| python-jose | ★★★★ | ★★★ | Active |",
       ConfidenceJustification="(1) No (2) No (3) No (4) No (5) No (6) No",
       ConfidenceScore=0.95
   )

State Persistence
-----------------

TaskToolSet automatically persists state to the agent's brain directory:

- Task boundaries and mode transitions
- Created and modified artifacts
- Tool call counters
- User notification history

State is restored when the agent reconnects, enabling continuation of long-running tasks.

Best Practices
--------------

1. **Call task_boundary first**: Always call it as the first tool in any batch
2. **Use %SAME% for updates**: Avoid repeating unchanged values
3. **Be concise in summaries**: Keep TaskSummary to 1-2 lines
4. **Accurate confidence scoring**: Answer all 6 questions honestly
5. **Use markdown in notifications**: Format messages for readability
6. **Set BlockedOnUser correctly**: True only when you need approval to proceed

