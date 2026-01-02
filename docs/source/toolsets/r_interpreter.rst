RInterpreterToolSet
===================

The RInterpreterToolSet provides agents with the ability to execute R code in persistent interpreter sessions with automatic session management and crash recovery.

Overview
--------

Key features:

* **Process Isolation**: Each interpreter runs in a separate R process
* **Session Management**: State persists across multiple executions
* **Plot Support**: Automatic figure capture and base64 encoding
* **Auto-Recovery**: Automatically restarts crashed interpreters
* **Timeout Support**: Configurable timeouts for long-running operations

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import RInterpreterToolSet

   # Create R interpreter toolset
   r_tools = RInterpreterToolSet(
       name="r",
       workdir="/path/to/workspace",  # Optional
       r_executable="R"               # Optional: path to R
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="statistician",
       instructions="You are a statistician who analyzes data using R.",
       model="gpt-4o"
   )
   await agent.toolset(r_tools)

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
   * - ``r_executable``
     - str
     - Path to R executable. Default: "R"
   * - ``r_args``
     - list[str] | None
     - Arguments to pass to R executable.
   * - ``init_code``
     - str | None
     - R code to run when initializing each interpreter.
   * - ``workdir``
     - str | None
     - Working directory for R sessions. Defaults to current directory.

Tools Reference
---------------

run_r_code
~~~~~~~~~~

Execute R code with automatic session management.

.. code-block:: python

   result = await r_tools.run_r_code(
       code="x <- 1:10; mean(x)",
       timeout=30  # Optional: timeout in seconds
   )

**Parameters:**

- ``code``: The R code to run
- ``timeout``: Optional timeout in seconds. Use None for no timeout.

**Returns:**

.. code-block:: python

   {
       "result": None,  # R doesn't return specific variables
       "stdout": "5.5\n",
       "stderr": "",
       "code_executed": "x <- 1:10; mean(x)"
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

Create a new R interpreter session.

.. code-block:: python

   result = await r_tools.new_interpreter()
   # Returns: {"interpreter_id": "abc123", "initial_output": "R version..."}

run_code_in_interpreter
~~~~~~~~~~~~~~~~~~~~~~~

Run R code in a specific interpreter session.

.. code-block:: python

   result = await r_tools.run_code_in_interpreter(
       code="summary(data)",
       interpreter_id="abc123",
       timeout=60  # Optional
   )
   # Returns: str (output from R)

delete_interpreter
~~~~~~~~~~~~~~~~~~

Delete an R interpreter session.

.. code-block:: python

   await r_tools.delete_interpreter(interpreter_id="abc123")

get_interpreter_output
~~~~~~~~~~~~~~~~~~~~~~

Get remaining output from an interpreter (useful after timeout).

.. code-block:: python

   output = await r_tools.get_interpreter_output(
       interpreter_id="abc123",
       timeout=10  # Optional
   )

Session Management
------------------

State Persistence
~~~~~~~~~~~~~~~~~

Variables persist across executions in the same session:

.. code-block:: python

   # First execution
   await r_tools.run_r_code("data <- mtcars")

   # Second execution - data is still available
   result = await r_tools.run_r_code("summary(data$mpg)")

Client Isolation
~~~~~~~~~~~~~~~~

Each client_id gets its own interpreter session automatically:

.. code-block:: python

   # Different clients have isolated R sessions
   # Client A: x <- 10
   # Client B: x <- 20  (separate session)

Auto-Recovery
~~~~~~~~~~~~~

If an interpreter crashes, it automatically restarts and reinitializes with the configured ``workdir`` and ``init_code``.

Examples
--------

Statistical Analysis
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = await r_tools.run_r_code("""
   # Load data
   data(mtcars)

   # T-test comparing manual vs automatic transmission
   manual <- mtcars$mpg[mtcars$am == 1]
   auto <- mtcars$mpg[mtcars$am == 0]
   t.test(manual, auto)
   """)

Data Visualization
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = await r_tools.run_r_code("""
   library(ggplot2)

   # Create scatter plot with regression line
   ggplot(mtcars, aes(x=wt, y=mpg)) +
       geom_point() +
       geom_smooth(method="lm") +
       labs(title="Weight vs MPG",
            x="Weight (1000 lbs)", y="Miles per Gallon") +
       theme_minimal()
   """)
   # result["base64_uri"] contains the plot image

Linear Regression
~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = await r_tools.run_r_code("""
   # Fit linear model
   model <- lm(mpg ~ wt + hp + am, data=mtcars)
   summary(model)

   # Model diagnostics
   par(mfrow=c(2,2))
   plot(model)
   """)

Time Series
~~~~~~~~~~~

.. code-block:: python

   result = await r_tools.run_r_code("""
   library(forecast)

   # Create time series
   ts_data <- ts(AirPassengers, frequency=12)

   # Fit ARIMA model
   model <- auto.arima(ts_data)
   forecast_result <- forecast(model, h=12)
   plot(forecast_result)
   """)

Initialization Code
~~~~~~~~~~~~~~~~~~~

Use ``init_code`` to pre-load packages:

.. code-block:: python

   r_tools = RInterpreterToolSet(
       name="r",
       init_code="""
       library(tidyverse)
       library(ggplot2)
       library(data.table)
       options(warn=-1)
       """
   )

Best Practices
--------------

1. **Use timeout for long operations**: Prevents blocking on slow computations
2. **Pre-load packages with init_code**: Faster subsequent executions
3. **Use run_r_code for most cases**: Handles session management automatically
4. **Set seeds for reproducibility**: ``set.seed(123)`` before random operations
5. **Run in containers**: The toolset executes arbitrary code - use isolated environments

Security Warning
----------------

This toolset can execute arbitrary R code. Always:

- Run in a sandboxed environment (Docker, VM)
- Limit agent instructions to specific tasks
- Monitor code execution
- Avoid exposing to untrusted input
