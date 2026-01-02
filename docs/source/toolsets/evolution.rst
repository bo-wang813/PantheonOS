EvolutionToolSet
================

The EvolutionToolSet provides evolutionary code optimization using iterative LLM-guided mutations and evaluations.

Overview
--------

Key features:

* **Single-File Evolution**: Optimize individual code files
* **Codebase Evolution**: Optimize multi-file projects
* **Island-Based Evolution**: Parallel populations for diversity
* **Custom Evaluators**: User-defined fitness functions
* **Progress Tracking**: Monitor evolution status and history

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import EvolutionToolSet

   # Create evolution toolset
   evolution_tools = EvolutionToolSet(
       name="evolution",
       workdir="/path/to/workspace",
       default_iterations=50,
       default_islands=3
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="optimizer",
       instructions="You help users optimize their code through evolution.",
       model="gpt-4o"
   )
   await agent.toolset(evolution_tools)

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
     - Name of the toolset (default: "evolution")
   * - ``workdir``
     - str | None
     - Working directory for evolution workspaces
   * - ``default_iterations``
     - int
     - Default number of evolution iterations (default: 50)
   * - ``default_islands``
     - int
     - Default number of evolution islands (default: 3)

Tools Reference
---------------

evolve_code
~~~~~~~~~~~

Evolve and optimize a single piece of code.

.. code-block:: python

   result = await evolution_tools.evolve_code(
       code="def sort(arr): ...",
       evaluator_code='''
   def evaluate(workspace_path):
       import time
       exec(open(f"{workspace_path}/main.py").read())
       # Run benchmarks...
       return {"combined_score": 0.85, "speed": 1.2}
   ''',
       objective="Optimize for speed while maintaining correctness",
       iterations=50,
       islands=3,
       model="normal"
   )

**Parameters:**

- ``code``: The initial code to optimize (single file content)
- ``evaluator_code``: Python code defining an ``evaluate(workspace_path)`` function
- ``objective``: Natural language description of the optimization goal
- ``iterations``: Maximum iterations (default: 50)
- ``islands``: Number of parallel populations (default: 3)
- ``model``: Model for mutation generation

**Returns:**

.. code-block:: python

   {
       "success": True,
       "best_code": "def sort(arr): ...",  # Optimized code
       "best_score": 0.95,
       "initial_score": 0.70,
       "improvement": 0.25,
       "total_iterations": 45,
       "improvements_found": 12,
       "summary": "Evolution completed..."
   }

evolve_codebase
~~~~~~~~~~~~~~~

Evolve an entire multi-file codebase.

.. code-block:: python

   result = await evolution_tools.evolve_codebase(
       codebase_path="/path/to/project",
       evaluator_code='''
   def evaluate(workspace_path):
       import subprocess
       result = subprocess.run(
           ["pytest", workspace_path],
           capture_output=True
       )
       passed = result.returncode == 0
       return {"combined_score": 1.0 if passed else 0.0}
   ''',
       objective="Improve test coverage and performance",
       include_patterns=["**/*.py"],
       output_path="/path/to/output"
   )

**Parameters:**

- ``codebase_path``: Path to the directory containing the codebase
- ``evaluator_code``: Python code defining an ``evaluate(workspace_path)`` function
- ``objective``: Natural language description of the optimization goal
- ``include_patterns``: Glob patterns for files to include (default: ["**/*.py"])
- ``iterations``: Maximum iterations
- ``islands``: Number of parallel populations
- ``model``: Model for mutation generation
- ``output_path``: Optional path to save the best result

**Returns:**

.. code-block:: python

   {
       "success": True,
       "best_score": 0.92,
       "initial_score": 0.75,
       "improvement": 0.17,
       "total_iterations": 50,
       "improvements_found": 8,
       "files_evolved": ["src/main.py", "src/utils.py"],
       "output_path": "/path/to/output",
       "summary": "Codebase evolution completed..."
   }

get_evolution_status
~~~~~~~~~~~~~~~~~~~~

Get the status of a saved evolution database.

.. code-block:: python

   result = await evolution_tools.get_evolution_status(
       database_path="/path/to/evolution.db"
   )

**Returns:**

.. code-block:: python

   {
       "success": True,
       "total_programs": 150,
       "best_score": 0.95,
       "avg_fitness": 0.82,
       "num_islands": 3,
       "archive_size": 25,
       "best_program_id": "prog_abc123",
       "best_generation": 42
   }

Writing Evaluators
------------------

Evaluators are Python functions that score code quality:

.. code-block:: python

   def evaluate(workspace_path):
       """
       Evaluate code quality.

       Args:
           workspace_path: Directory containing the code to evaluate

       Returns:
           dict with at least "combined_score" (0-1 scale)
       """
       # Read the code
       with open(f"{workspace_path}/main.py") as f:
           code = f.read()

       # Run tests, benchmarks, or analysis
       score = 0.0

       # Check correctness
       try:
           exec(code)
           score += 0.5
       except:
           pass

       # Measure performance
       import time
       start = time.time()
       # ... run benchmark ...
       elapsed = time.time() - start

       if elapsed < 0.1:
           score += 0.3

       # Check code quality
       if len(code) < 1000:  # Prefer concise code
           score += 0.2

       return {
           "combined_score": score,  # Required
           "correctness": 0.5,       # Optional metrics
           "speed": elapsed,
           "complexity": len(code)
       }

Examples
--------

Optimizing a Sorting Algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   initial_code = '''
   def sort(arr):
       for i in range(len(arr)):
           for j in range(i + 1, len(arr)):
               if arr[i] > arr[j]:
                   arr[i], arr[j] = arr[j], arr[i]
       return arr
   '''

   evaluator = '''
   def evaluate(workspace_path):
       import time
       import random

       exec(open(f"{workspace_path}/main.py").read(), globals())

       # Test correctness
       test_cases = [
           ([3, 1, 2], [1, 2, 3]),
           ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5]),
           ([], []),
       ]

       correct = all(sort(list(t[0])) == t[1] for t in test_cases)
       if not correct:
           return {"combined_score": 0.0}

       # Benchmark speed
       test_data = [random.randint(0, 1000) for _ in range(1000)]
       start = time.time()
       sort(test_data)
       elapsed = time.time() - start

       # Score: faster is better (0.01s = 1.0, 1s = 0.1)
       speed_score = min(1.0, 0.01 / elapsed)

       return {"combined_score": speed_score, "time": elapsed}
   '''

   result = await evolution_tools.evolve_code(
       code=initial_code,
       evaluator_code=evaluator,
       objective="Optimize sorting speed while maintaining correctness",
       iterations=100
   )

Best Practices
--------------

1. **Start with working code**: Initial code should pass basic tests
2. **Clear objectives**: Be specific about optimization goals
3. **Robust evaluators**: Handle errors gracefully in evaluator code
4. **Use multiple islands**: Increases diversity and exploration
5. **Monitor progress**: Check intermediate results via evolution status
6. **Save outputs**: Use ``output_path`` to preserve best results

Security Warning
----------------

Evolution executes arbitrary code during evaluation. Always:

- Run in sandboxed environments (Docker, VM)
- Limit evaluator permissions
- Monitor resource usage
- Avoid untrusted code inputs
