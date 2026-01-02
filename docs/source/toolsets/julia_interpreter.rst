JuliaInterpreterToolSet
=======================

The JuliaInterpreterToolSet provides agents with the ability to execute Julia code in persistent interpreter sessions with automatic crash recovery and figure capture.

Overview
--------

Key features:

* **Process Isolation**: Each interpreter runs in a separate Julia process
* **Session Management**: State persists across multiple executions
* **Figure Support**: Automatic plot capture and base64 encoding
* **Auto-Recovery**: Automatically restarts crashed interpreters
* **Timeout Support**: Configurable timeouts for long-running operations

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import JuliaInterpreterToolSet

   # Create Julia interpreter toolset
   julia_tools = JuliaInterpreterToolSet(
       name="julia",
       workdir="/path/to/workspace",
       julia_executable="julia"  # Path to Julia executable
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="scientist",
       instructions="You are a scientist who analyzes data using Julia.",
       model="gpt-4o"
   )
   await agent.toolset(julia_tools)

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
   * - ``julia_executable``
     - str
     - Path to Julia executable. Default: "julia"
   * - ``julia_args``
     - list[str] | None
     - Arguments to pass to Julia executable
   * - ``init_code``
     - str | None
     - Julia code to run when initializing each interpreter
   * - ``workdir``
     - str | None
     - Working directory for Julia sessions. Defaults to current directory.

Tools Reference
---------------

run_julia_code
~~~~~~~~~~~~~~

Execute Julia code with automatic session management.

.. code-block:: python

   result = await julia_tools.run_julia_code(
       code="x = 1:10; mean(x)",
       timeout=30  # Optional: timeout in seconds
   )

**Parameters:**

- ``code``: The Julia code to run
- ``timeout``: Optional timeout in seconds. Use None for no timeout (long-running commands).

**Returns:**

.. code-block:: python

   {
       "result": None,
       "stdout": "5.5\n",
       "stderr": "",
       "code_executed": "x = 1:10; mean(x)"
   }

**Figure Output:**

When code generates plots, they are automatically captured:

.. code-block:: python

   {
       "result": None,
       "stdout": "...",
       "stderr": "",
       "fig_storage_path": "/tmp/abc123.png",
       "base64_uri": ["data:image/png;base64,..."]
   }

new_interpreter
~~~~~~~~~~~~~~~

Create a new Julia interpreter session.

.. code-block:: python

   result = await julia_tools.new_interpreter()
   # Returns: {"interpreter_id": "abc123", "initial_output": "Julia version..."}

run_code_in_interpreter
~~~~~~~~~~~~~~~~~~~~~~~

Run Julia code in a specific interpreter session.

.. code-block:: python

   result = await julia_tools.run_code_in_interpreter(
       code="println(x * 2)",
       interpreter_id="abc123",
       timeout=60
   )
   # Returns: str (output from Julia)

delete_interpreter
~~~~~~~~~~~~~~~~~~

Delete a Julia interpreter session.

.. code-block:: python

   await julia_tools.delete_interpreter(interpreter_id="abc123")

get_interpreter_output
~~~~~~~~~~~~~~~~~~~~~~

Get remaining output from an interpreter (useful after timeout).

.. code-block:: python

   output = await julia_tools.get_interpreter_output(
       interpreter_id="abc123",
       timeout=10
   )

Session Management
------------------

State Persistence
~~~~~~~~~~~~~~~~~

Variables persist across executions in the same session:

.. code-block:: python

   # First execution
   await julia_tools.run_julia_code("data = rand(100)")

   # Second execution - data is still available
   result = await julia_tools.run_julia_code("mean(data)")

Auto-Recovery
~~~~~~~~~~~~~

If an interpreter crashes, it automatically restarts and reinitializes:

.. code-block:: python

   {
       "result": None,
       "stdout": "[Info] Julia interpreter was restarted...\nOutput here",
       "stderr": "",
       "code_executed": "...",
       "interpreter_crashed": True  # Only on crash
   }

Figure Saving
~~~~~~~~~~~~~

Use the built-in ``save_figure`` function:

.. code-block:: julia

   using Plots
   plot(1:10, rand(10))
   save_figure("my_plot.png")

Examples
--------

Statistical Analysis
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = await julia_tools.run_julia_code("""
   using Statistics

   # Generate sample data
   data = randn(1000)

   # Compute statistics
   println("Mean: ", mean(data))
   println("Std: ", std(data))
   println("Median: ", median(data))
   """)

Data Visualization
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = await julia_tools.run_julia_code("""
   using Plots

   x = 0:0.1:10
   y = sin.(x)

   plot(x, y,
       title="Sine Wave",
       xlabel="x",
       ylabel="sin(x)",
       legend=false)
   save_figure("sine_wave.png")
   """)
   # result["base64_uri"] contains the plot image

Scientific Computing
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = await julia_tools.run_julia_code("""
   using LinearAlgebra
   using DifferentialEquations

   # Solve simple ODE: du/dt = -u
   f(u, p, t) = -u
   u0 = 1.0
   tspan = (0.0, 5.0)

   prob = ODEProblem(f, u0, tspan)
   sol = solve(prob)

   println("Solution at t=5: ", sol(5.0))
   """)

Initialization Code
~~~~~~~~~~~~~~~~~~~

Use ``init_code`` to pre-load packages:

.. code-block:: python

   julia_tools = JuliaInterpreterToolSet(
       name="julia",
       init_code="""
       using Statistics
       using LinearAlgebra
       using Plots
       gr()  # Use GR backend
       """
   )

Best Practices
--------------

1. **Use timeout for long operations**: Prevents blocking on slow computations
2. **Pre-load packages with init_code**: Faster subsequent executions
3. **Use run_julia_code for most cases**: Handles session management automatically
4. **Set seeds for reproducibility**: ``Random.seed!(123)`` before random operations
5. **Run in containers**: The toolset executes arbitrary code - use isolated environments

Security Warning
----------------

This toolset can execute arbitrary Julia code. Always:

- Run in a sandboxed environment (Docker, VM)
- Limit agent instructions to specific tasks
- Monitor code execution
- Avoid exposing to untrusted input
