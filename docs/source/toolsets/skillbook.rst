SkillbookToolSet
================

The SkillbookToolSet provides skill management capabilities for the Skill Learning system, enabling agents to learn, store, and apply knowledge from conversations.

Overview
--------

Key features:

* **Skill Management**: Add, update, remove, and tag skills
* **Section Organization**: Categorize skills by type (user_rules, strategies, patterns, workflows)
* **Confidence Filtering**: Only accept skills above a confidence threshold
* **Feedback Tracking**: Track helpful/harmful/neutral feedback for quality assessment
* **Agent Scoping**: Skills can be global or agent-specific

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import SkillbookToolSet

   # Create skillbook toolset
   skillbook_tools = SkillbookToolSet(
       name="skillbook",
       min_confidence=0.7
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="skill_manager",
       instructions="You manage and learn from conversations.",
       model="gpt-4o"
   )
   await agent.toolset(skillbook_tools)

   await agent.chat()

Constructor Parameters
----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Parameter
     - Type
     - Description
   * - ``skillbook``
     - Skillbook | None
     - Skillbook instance to manage. Auto-creates if None.
   * - ``min_confidence``
     - float
     - Minimum confidence threshold for adding skills (default: 0.7)
   * - ``name``
     - str
     - Name of the toolset (default: "skillbook")

Tools Reference
---------------

add_skill
~~~~~~~~~

Add a new skill to the skillbook.

.. code-block:: python

   result = skillbook_tools.add_skill(
       section="strategies",
       content="Use polars lazy evaluation for memory-efficient large file processing",
       description="Polars lazy eval for large files",
       agent_name="data_analyst",
       confidence=0.9
   )

**Parameters:**

- ``section``: Category - "user_rules", "strategies", "patterns", or "workflows"
- ``content``: The skill content (specific and actionable)
- ``description``: Short summary (max 15 words) for long content
- ``agent_name``: Agent scope - "global" for all agents or specific name
- ``sources``: Optional list of temp file paths with examples/documentation
- ``skill_id``: Custom ID (auto-generated if omitted)
- ``confidence``: Confidence level 0.0-1.0 (must exceed min_confidence)

**Returns:**

.. code-block:: python

   {"success": True, "skill_id": "str-a1b2c3d4", "message": "Added skill..."}

update_skill
~~~~~~~~~~~~

Update an existing skill's content or sources.

.. code-block:: python

   result = skillbook_tools.update_skill(
       skill_id="str-a1b2c3d4",
       content="Updated skill content here",
       description="Updated description"
   )

**Parameters:**

- ``skill_id``: ID of the skill to update
- ``content``: New content (None to keep unchanged)
- ``description``: New description (None to keep unchanged)
- ``sources``: New source files (replaces existing)

remove_skill
~~~~~~~~~~~~

Permanently remove a skill.

.. code-block:: python

   result = skillbook_tools.remove_skill(skill_id="str-a1b2c3d4")

tag_skill
~~~~~~~~~

Record feedback on a skill's effectiveness.

.. code-block:: python

   result = skillbook_tools.tag_skill(
       skill_id="str-a1b2c3d4",
       tag="helpful"  # or "harmful" or "neutral"
   )

**Returns:**

.. code-block:: python

   {
       "success": True,
       "skill_id": "str-a1b2c3d4",
       "stats": "+3/-1/~0",  # helpful/harmful/neutral counts
       "message": "Tagged skill..."
   }

list_skills
~~~~~~~~~~~

List and filter skills in the skillbook.

.. code-block:: python

   result = skillbook_tools.list_skills(
       section="strategies",
       tag="helpful",
       keyword="polars",
       include_full_content=False
   )

**Parameters:**

- ``section``: Filter by category (None for all)
- ``tag``: Filter by dominant feedback ("helpful", "harmful", "neutral")
- ``keyword``: Case-insensitive search in content
- ``include_full_content``: Return complete content (default: truncated)

**Returns:**

.. code-block:: python

   {
       "total": 5,
       "filters": {"section": "strategies", ...},
       "skills": [
           {
               "id": "str-a1b2c3d4",
               "section": "strategies",
               "content": "Use polars lazy eval...",
               "sources": [],
               "stats": "+3/-0/~1"
           }
       ]
   }

compress_trajectory
~~~~~~~~~~~~~~~~~~~

Compress a conversation memory for analysis.

.. code-block:: python

   result = skillbook_tools.compress_trajectory(
       memory_path="/tmp/memory.json",
       output_dir="/tmp/analysis"
   )

**Returns:**

.. code-block:: python

   {
       "success": True,
       "trajectory_path": "/tmp/analysis/trajectory_xxx.txt",
       "details_path": "/tmp/memory.json",
       "skill_ids_cited": ["str-xxx", "pat-yyy"]
   }

get_skillbook_content
~~~~~~~~~~~~~~~~~~~~~

Get formatted skillbook content for injection.

.. code-block:: python

   result = skillbook_tools.get_skillbook_content(agent_name="global")

Skill Sections
--------------

Skills are organized into four sections:

- **user_rules**: User preferences and explicit instructions
- **strategies**: Problem-solving approaches and methodologies
- **patterns**: Reusable code patterns and templates
- **workflows**: Multi-step procedures and pipelines

Examples
--------

Learning from a Conversation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # After successful task completion
   result = skillbook_tools.add_skill(
       section="strategies",
       content="When processing large CSV files with polars, use scan_csv() "
               "instead of read_csv() for streaming to avoid memory issues",
       agent_name="data_analyst",
       confidence=0.9
   )

Reviewing Skills
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Find helpful strategies
   result = skillbook_tools.list_skills(
       section="strategies",
       tag="helpful"
   )

   # Search for specific topics
   result = skillbook_tools.list_skills(keyword="polars")

Providing Feedback
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # After a skill helped
   skillbook_tools.tag_skill(skill_id="str-abc123", tag="helpful")

   # After a skill caused issues
   skillbook_tools.tag_skill(skill_id="str-xyz789", tag="harmful")

Analyzing Conversations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Compress conversation for analysis
   result = skillbook_tools.compress_trajectory(
       memory_path="/path/to/memory.json"
   )

   # Check which skills were referenced
   print(f"Skills cited: {result['skill_ids_cited']}")

Best Practices
--------------

1. **Check before adding**: Use ``list_skills`` to avoid duplicates
2. **Be specific**: Write actionable, concrete skills
3. **Use confidence scores**: Only add skills you're confident about
4. **Provide feedback**: Tag skills after observing their effectiveness
5. **Organize by section**: Choose appropriate categories for skills
6. **Scope appropriately**: Use agent-specific scopes when relevant
