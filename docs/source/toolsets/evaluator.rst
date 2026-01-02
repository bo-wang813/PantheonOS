EvaluatorToolSet
================

The EvaluatorToolSet provides code evaluation and quality assessment tools for analyzing code quality, running custom evaluators, and getting LLM-based code reviews.

Overview
--------

Key features:

* **Custom Evaluators**: Run user-defined evaluation functions
* **Static Metrics**: Compute complexity, diversity, and line counts
* **LLM Code Review**: Get AI-powered code quality assessments
* **Timeout Support**: Configurable timeouts for evaluations

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import EvaluatorToolSet

   # Create evaluator toolset
   eval_tools = EvaluatorToolSet(
       name="evaluator",
       workdir="/path/to/workspace",
       timeout=120
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="code_reviewer",
       instructions="You analyze and evaluate code quality.",
       model="gpt-4o"
   )
   await agent.toolset(eval_tools)

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
     - Name of the toolset (default: "evaluator")
   * - ``workdir``
     - str | None
     - Working directory for evaluation workspaces
   * - ``timeout``
     - int
     - Default timeout for evaluations in seconds (default: 120)

Tools Reference
---------------

evaluate_code
~~~~~~~~~~~~~

Evaluate a piece of code using a custom evaluator function.

.. code-block:: python

   result = await eval_tools.evaluate_code(
       code="def add(a, b): return a + b",
       evaluator_code='''
   def evaluate(workspace_path):
       exec(open(f"{workspace_path}/main.py").read(), globals())
       tests_passed = add(1, 2) == 3 and add(-1, 1) == 0
       return {"combined_score": 1.0 if tests_passed else 0.0}
   ''',
       filename="main.py",
       timeout=60
   )

**Parameters:**

- ``code``: The code to evaluate
- ``evaluator_code``: Python code defining an ``evaluate(workspace_path)`` function
- ``filename``: Name of the file to save the code as (default: "main.py")
- ``timeout``: Evaluation timeout in seconds (default: 120)

**Returns:**

.. code-block:: python

   {
       "success": True,
       "metrics": {"combined_score": 1.0, "tests_passed": 2},
       "combined_score": 1.0
   }

evaluate_codebase
~~~~~~~~~~~~~~~~~

Evaluate an entire codebase using a custom evaluator.

.. code-block:: python

   result = await eval_tools.evaluate_codebase(
       codebase_path="/path/to/project",
       evaluator_code='''
   def evaluate(workspace_path):
       import subprocess
       result = subprocess.run(["pytest", workspace_path], capture_output=True)
       return {"combined_score": 1.0 if result.returncode == 0 else 0.0}
   ''',
       timeout=300
   )

**Parameters:**

- ``codebase_path``: Path to the codebase directory
- ``evaluator_code``: Python code defining an ``evaluate(workspace_path)`` function
- ``timeout``: Evaluation timeout in seconds

**Returns:**

.. code-block:: python

   {
       "success": True,
       "metrics": {"combined_score": 0.85, "tests_passed": 17, "tests_total": 20},
       "combined_score": 0.85
   }

compute_code_metrics
~~~~~~~~~~~~~~~~~~~~

Compute static code metrics for analysis.

.. code-block:: python

   result = await eval_tools.compute_code_metrics(
       code='''
   class Calculator:
       def add(self, a, b):
           return a + b

       def multiply(self, a, b):
           return a * b
   '''
   )

**Returns:**

.. code-block:: python

   {
       "success": True,
       "complexity": 0.25,          # Cyclomatic complexity score (0-1)
       "diversity": 0.65,           # Code diversity score (0-1)
       "total_lines": 8,
       "code_lines": 6,             # Non-empty, non-comment lines
       "num_functions": 2,
       "num_classes": 1,
       "avg_function_length": 2.0
   }

get_llm_code_review
~~~~~~~~~~~~~~~~~~~

Get an LLM-based code review with quality scores and suggestions.

.. code-block:: python

   result = await eval_tools.get_llm_code_review(
       code='''
   def process_data(data):
       result = []
       for item in data:
           if item > 0:
               result.append(item * 2)
       return result
   ''',
       context="This function processes numerical data",
       model="normal"
   )

**Parameters:**

- ``code``: The code to review
- ``context``: Optional context about what the code does
- ``model``: Model to use for the review

**Returns:**

.. code-block:: python

   {
       "success": True,
       "score": 75,
       "issues": [
           "Could use list comprehension for conciseness",
           "Missing type hints"
       ],
       "suggestions": [
           "Use: [item * 2 for item in data if item > 0]",
           "Add type hints: def process_data(data: list[int]) -> list[int]"
       ],
       "summary": "Functional code but could be more Pythonic"
   }

Writing Evaluators
------------------

Evaluator functions must follow this pattern:

.. code-block:: python

   def evaluate(workspace_path):
       """
       Evaluate code quality.

       Args:
           workspace_path: Directory containing the code to evaluate

       Returns:
           dict with at least "combined_score" (0-1 scale)
       """
       # Read code files
       with open(f"{workspace_path}/main.py") as f:
           code = f.read()

       # Run tests, benchmarks, or analysis
       # ...

       return {
           "combined_score": 0.85,  # Required: 0-1 scale
           "custom_metric": 42,     # Optional: additional metrics
       }

Examples
--------

Testing a Function
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   code = '''
   def fibonacci(n):
       if n <= 1:
           return n
       return fibonacci(n-1) + fibonacci(n-2)
   '''

   evaluator = '''
   def evaluate(workspace_path):
       exec(open(f"{workspace_path}/main.py").read(), globals())

       # Test cases
       tests = [
           (0, 0), (1, 1), (5, 5), (10, 55)
       ]

       passed = sum(1 for n, expected in tests if fibonacci(n) == expected)
       return {
           "combined_score": passed / len(tests),
           "tests_passed": passed,
           "tests_total": len(tests)
       }
   '''

   result = await eval_tools.evaluate_code(
       code=code,
       evaluator_code=evaluator
   )

Comprehensive Code Review
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get static metrics
   metrics = await eval_tools.compute_code_metrics(code=my_code)

   # Get LLM review
   review = await eval_tools.get_llm_code_review(
       code=my_code,
       context="Authentication middleware for Express.js"
   )

   # Combine insights
   print(f"Complexity: {metrics['complexity']}")
   print(f"Quality Score: {review['score']}/100")
   print(f"Issues: {review['issues']}")

Best Practices
--------------

1. **Set appropriate timeouts**: Long evaluations should have higher timeouts
2. **Handle errors in evaluators**: Use try/except to avoid crashes
3. **Return meaningful scores**: Use 0-1 scale with clear semantics
4. **Add custom metrics**: Include additional metrics beyond combined_score
5. **Use LLM reviews for context**: Get human-readable feedback
6. **Combine static + dynamic**: Use both metrics and custom evaluators

Security Warning
----------------

Evaluators execute arbitrary code. Always:

- Run in sandboxed environments (Docker, VM)
- Limit file system access
- Set appropriate timeouts
- Monitor resource usage
