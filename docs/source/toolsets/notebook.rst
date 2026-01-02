IntegratedNotebookToolSet
=========================

The IntegratedNotebookToolSet provides full Jupyter notebook operations with integrated kernel management, cell-based editing, and code execution.

Overview
--------

Key features:

* **Notebook Management**: Create, open, and manage notebook files
* **Cell Operations**: Add, update, delete, move cells with cell_id-based addressing
* **Code Execution**: Execute Python, R (via %%R magic), and shell (via %%bash)
* **Kernel Management**: Restart, interrupt, and monitor kernel state
* **Auto-Recovery**: Automatic kernel recovery after crashes

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import IntegratedNotebookToolSet

   # Create notebook toolset
   notebook_tools = IntegratedNotebookToolSet(
       name="notebook",
       workdir="/path/to/notebooks"  # Optional
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="analyst",
       instructions="You are a data analyst. Use Jupyter notebooks for analysis.",
       model="gpt-4o"
   )
   await agent.toolset(notebook_tools)

   await agent.chat()

Constructor Parameters
----------------------

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Parameter
     - Type
     - Description
   * - ``name``
     - str
     - Name of the toolset
   * - ``workdir``
     - str | None
     - Working directory for notebooks. Defaults to current directory.
   * - ``remote_backend``
     - RemoteBackend | None
     - Optional backend for streaming execution output.
   * - ``streaming_mode``
     - "auto" | "remote" | "local"
     - IOPub streaming mode. Default: "auto".

Tools Reference
---------------

create_notebook
~~~~~~~~~~~~~~~

Create or open a notebook file.

.. code-block:: python

   result = await notebook_tools.create_notebook(
       notebook_path="analysis.ipynb"
   )
   # Returns: {"success": True, "notebook_path": "...", "action": "created"|"opened"}

add_cell
~~~~~~~~

Add a new cell to the notebook.

.. code-block:: python

   result = await notebook_tools.add_cell(
       notebook_path="analysis.ipynb",
       cell_type="code",              # "code", "markdown", or "raw"
       content="import pandas as pd",
       cell_id="cell_1",              # Optional: auto-generated if not provided
       position=None,                  # Optional: index, cell_id, or None (append)
       execute=True                    # Execute after adding (recommended for code)
   )

**Position options:**

- ``None``: Append to end (default)
- ``"0"``, ``"1"``: Insert at index (0-based)
- ``"cell_id"``: Insert after the cell with this ID

execute_cell
~~~~~~~~~~~~

Execute an existing cell's content.

.. code-block:: python

   result = await notebook_tools.execute_cell(
       notebook_path="analysis.ipynb",
       cell_id="cell_1"
   )
   # Returns: {"success": True, "output": "...", "kernel_session_id": "..."}

**Supported syntax:**

- Python code (default)
- R language: ``%%R`` (cell magic) or ``%R`` (line magic)
- Shell commands: ``%%bash`` or ``%%sh``
- Other magics: ``%%time``, ``%%html``, ``%matplotlib inline``, etc.

update_cell
~~~~~~~~~~~

Update cell content with optional execution.

.. code-block:: python

   # Full replacement
   result = await notebook_tools.update_cell(
       notebook_path="analysis.ipynb",
       cell_id="cell_1",
       content="x = 10",
       execute=True
   )

   # Partial replacement
   result = await notebook_tools.update_cell(
       notebook_path="analysis.ipynb",
       cell_id="cell_1",
       content="n_neighbors=30",
       old_content="n_neighbors=15",
       execute=True
   )
   # Returns: {"success": True, "replacements": 1, ...}

delete_cell
~~~~~~~~~~~

Delete a cell from the notebook.

.. code-block:: python

   result = await notebook_tools.delete_cell(
       notebook_path="analysis.ipynb",
       cell_id="cell_1"
   )

move_cell
~~~~~~~~~

Move a cell to a different position.

.. code-block:: python

   result = await notebook_tools.move_cell(
       notebook_path="analysis.ipynb",
       cell_id="cell_3",
       below_cell_id="cell_1"  # Move after cell_1 (None = move to top)
   )

read_cells
~~~~~~~~~~

Read cells with execution status and optional content.

.. code-block:: python

   # Get cell summaries
   result = await notebook_tools.read_cells(
       notebook_path="analysis.ipynb"
   )

   # Get full cell content
   result = await notebook_tools.read_cells(
       notebook_path="analysis.ipynb",
       include_details=True
   )

   # Read specific cells only
   result = await notebook_tools.read_cells(
       notebook_path="analysis.ipynb",
       include_details=True,
       cell_ids=["cell_1", "cell_3"]
   )

**Returns:**

.. code-block:: python

   {
       "success": True,
       "cells": [
           {
               "cell_id": "cell_1",
               "cell_index": 0,
               "cell_type": "code",
               "execution_count": 1,
               "execution_status": "success",  # or "error", "not_executed"
               "source_preview": "import pandas...",  # when include_details=False
               "source": "import pandas as pd",  # when include_details=True
               "outputs": [...]  # when include_details=True
           }
       ]
   }

list_notebooks
~~~~~~~~~~~~~~

List running notebooks for the current session.

.. code-block:: python

   result = await notebook_tools.list_notebooks()
   # Returns: {"success": True, "notebooks": [...], "count": 2}

manage_kernel
~~~~~~~~~~~~~

Unified kernel management operations.

.. code-block:: python

   # Restart kernel (clears all state)
   result = await notebook_tools.manage_kernel(
       notebook_path="analysis.ipynb",
       action="restart"
   )

   # Interrupt running execution
   result = await notebook_tools.manage_kernel(
       notebook_path="analysis.ipynb",
       action="interrupt"
   )

   # Get kernel status
   result = await notebook_tools.manage_kernel(
       notebook_path="analysis.ipynb",
       action="status"
   )

   # Get current kernel variables
   result = await notebook_tools.manage_kernel(
       notebook_path="analysis.ipynb",
       action="variables"
   )

   # Shutdown kernel (context preserved)
   result = await notebook_tools.manage_kernel(
       notebook_path="analysis.ipynb",
       action="shutdown"
   )

   # Delete context completely
   result = await notebook_tools.manage_kernel(
       notebook_path="analysis.ipynb",
       action="delete"
   )

R Language Support
------------------

Use R via the ``%%R`` magic (requires rpy2):

.. code-block:: python

   await notebook_tools.add_cell(
       "analysis.ipynb",
       "code",
       content="""%%R
   library(ggplot2)
   data(mtcars)
   ggplot(mtcars, aes(x=mpg, y=hp)) + geom_point()
   """,
       execute=True
   )

Pass data between Python and R:

.. code-block:: python

   # Python to R: %%R -i variable_name
   # R to Python: %%R -o variable_name

Examples
--------

Data Analysis Workflow
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import IntegratedNotebookToolSet

   notebook_tools = IntegratedNotebookToolSet(name="notebook")

   analyst = Agent(
       name="analyst",
       instructions="""You are a data analyst. When analyzing data:
       1. Create a notebook for the analysis
       2. Import required libraries
       3. Load and explore data
       4. Create visualizations
       5. Document findings in markdown cells""",
       model="gpt-4o"
   )
   await analyst.toolset(notebook_tools)

   # Agent creates notebook and performs analysis
   result = await analyst.run(
       "Analyze the iris dataset and create visualizations"
   )

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create notebook
   await notebook_tools.create_notebook("demo.ipynb")

   # Add import cell and execute
   await notebook_tools.add_cell(
       "demo.ipynb",
       cell_type="code",
       content="import numpy as np\nimport matplotlib.pyplot as plt",
       execute=True
   )

   # Add markdown documentation
   await notebook_tools.add_cell(
       "demo.ipynb",
       cell_type="markdown",
       content="# Sine Wave Plot\nGenerating a simple sine wave."
   )

   # Add visualization code
   await notebook_tools.add_cell(
       "demo.ipynb",
       cell_type="code",
       content="""x = np.linspace(0, 10, 100)
   y = np.sin(x)
   plt.plot(x, y)
   plt.title('Sine Wave')
   plt.show()""",
       execute=True
   )

   # Check cell status
   cells = await notebook_tools.read_cells("demo.ipynb")

Best Practices
--------------

1. **Use execute=True**: Execute code cells immediately when adding/updating
2. **Use cell_id addressing**: More stable than index-based addressing
3. **Document with markdown**: Add markdown cells for documentation
4. **Check execution status**: Use read_cells to verify cell execution
5. **Interrupt long operations**: Use manage_kernel(action="interrupt")
6. **Split long operations**: Break into multiple cells for better control
