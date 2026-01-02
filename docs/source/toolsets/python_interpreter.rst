PythonInterpreterToolSet
========================

The PythonInterpreterToolSet provides agents with the ability to execute Python code in isolated interpreter sessions with automatic session management and crash recovery.

Overview
--------

Key features:

* **Process Isolation**: Each interpreter runs in a separate process
* **Session Management**: State persists across multiple executions
* **Matplotlib Support**: Automatic plot capture and base64 encoding
* **Auto-Recovery**: Automatically restarts crashed interpreters
* **Echo Mode**: Expressions are automatically printed

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import PythonInterpreterToolSet

   # Create Python interpreter toolset
   python_tools = PythonInterpreterToolSet(
       name="python",
       workdir="/path/to/workspace"  # Optional
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="data_scientist",
       instructions="You are a data scientist who can analyze data with Python.",
       model="gpt-4o"
   )
   await agent.toolset(python_tools)

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
     - Name of the toolset
   * - ``workdir``
     - str | None
     - Working directory for the interpreter. Defaults to current directory.
   * - ``engine``
     - Engine | None
     - Optional executor engine for process pools.
   * - ``init_code``
     - str | None
     - Initialization code run when interpreter starts. Defaults to matplotlib setup.

Tools Reference
---------------

run_python_code
~~~~~~~~~~~~~~~

Execute Python code with automatic session management.

.. code-block:: python

   result = await python_tools.run_python_code(
       code="x = 1 + 2\nprint(x)",
       result_var_name="x"  # Optional: return value of this variable
   )

**Parameters:**

- ``code``: The Python code to run
- ``result_var_name``: Optional. Variable name to return the value of.
- ``interpreter_id``: Optional. Specific interpreter session to use.

**Returns:**

.. code-block:: python

   {
       "success": True,
       "result": 3,          # Value of result_var_name (if specified)
       "stdout": "3\n",      # Captured stdout
       "stderr": ""          # Captured stderr
   }

**Auto-Recovery:**

If the interpreter crashes, it automatically restarts:

.. code-block:: python

   {
       "success": True,
       "result": ...,
       "interpreter_restarted": True,
       "restart_reason": "BrokenProcessPool: ..."
   }

manage_interpreters
~~~~~~~~~~~~~~~~~~~

Manage interpreter sessions (create, list, delete).

.. code-block:: python

   # Create new interpreter
   result = await python_tools.manage_interpreters(operation="create")
   # Returns: {"success": True, "interpreter_id": "abc123"}

   # List all interpreters
   result = await python_tools.manage_interpreters(operation="list")
   # Returns: {"success": True, "interpreters": [{"id": "abc123", "status": "running"}]}

   # Delete interpreter
   result = await python_tools.manage_interpreters(
       operation="delete",
       interpreter_id="abc123"
   )

Session Management
------------------

State Persistence
~~~~~~~~~~~~~~~~~

Variables persist across executions in the same session:

.. code-block:: python

   # First execution
   await python_tools.run_python_code("x = 10")

   # Second execution - x is still available
   result = await python_tools.run_python_code("print(x * 2)")
   # stdout: "20"

Client Isolation
~~~~~~~~~~~~~~~~

Each client_id gets its own interpreter session automatically:

.. code-block:: python

   # Different clients have isolated sessions
   # Client A: x = 10
   # Client B: x = 20  (separate session)

Matplotlib Support
------------------

Plots are automatically captured and returned as base64 images:

.. code-block:: python

   result = await python_tools.run_python_code("""
   import matplotlib.pyplot as plt
   import numpy as np

   x = np.linspace(0, 10, 100)
   y = np.sin(x)
   plt.plot(x, y)
   plt.title('Sine Wave')
   plt.show()
   """)

   # Result includes:
   # result["fig_storage_path"] = ".matplotlib_figs/abc123.png"
   # result["base64_uri"] = ["data:image/png;base64,..."]

Available Libraries
-------------------

The interpreter includes common data science libraries:

- **Data Analysis**: pandas, numpy, scipy
- **Visualization**: matplotlib, seaborn, plotly
- **Machine Learning**: scikit-learn, statsmodels
- **Utilities**: datetime, collections, json

Examples
--------

Data Analysis
~~~~~~~~~~~~~

.. code-block:: python

   result = await python_tools.run_python_code("""
   import pandas as pd
   import numpy as np

   # Create sample data
   df = pd.DataFrame({
       'date': pd.date_range('2024-01-01', periods=30),
       'sales': np.random.randint(100, 1000, 30),
       'region': np.random.choice(['North', 'South', 'East'], 30)
   })

   # Analyze
   summary = df.groupby('region')['sales'].agg(['mean', 'sum'])
   print(summary)
   """)

Machine Learning
~~~~~~~~~~~~~~~~

.. code-block:: python

   result = await python_tools.run_python_code("""
   from sklearn.model_selection import train_test_split
   from sklearn.linear_model import LinearRegression
   from sklearn.metrics import r2_score
   import numpy as np

   # Generate sample data
   X = np.random.rand(100, 1) * 10
   y = 2 * X + 1 + np.random.randn(100, 1) * 2

   # Train model
   X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
   model = LinearRegression()
   model.fit(X_train, y_train)

   # Evaluate
   predictions = model.predict(X_test)
   r2 = r2_score(y_test, predictions)
   print(f"R² Score: {r2:.4f}")
   """)

Returning Values
~~~~~~~~~~~~~~~~

Use ``result_var_name`` to get specific variable values:

.. code-block:: python

   result = await python_tools.run_python_code(
       code="""
       import pandas as pd
       df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
       summary = df.describe().to_dict()
       """,
       result_var_name="summary"
   )
   # result["result"] contains the summary dictionary

Best Practices
--------------

1. **Use result_var_name for structured data**: Get dictionaries/lists back directly
2. **Print intermediate results**: Helps debugging and visibility
3. **Handle errors in code**: Use try/except for robust scripts
4. **Keep sessions for related work**: Reuse state across related operations
5. **Run in containers**: Interpreter can execute arbitrary code

Security Warning
----------------

This toolset can execute arbitrary Python code. Always:

- Run in a sandboxed environment (Docker, VM)
- Limit agent instructions to specific tasks
- Monitor code execution
- Avoid exposing to untrusted input
