CodeToolSet
===========

The CodeToolSet provides code navigation and exploration tools using tree-sitter for multi-language AST parsing.

Overview
--------

Key features:

* **File Outlines**: View structured overviews of classes and functions
* **Symbol Extraction**: Get source code for specific symbols
* **Multi-Language Support**: Python, JavaScript, TypeScript, JSX, TSX
* **Efficient Navigation**: Navigate large codebases without reading entire files

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import CodeToolSet

   # Create code toolset
   code_tools = CodeToolSet(
       name="code",
       workspace_path="/path/to/project"
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="code_explorer",
       instructions="You can explore and understand code structure.",
       model="gpt-4o"
   )
   await agent.toolset(code_tools)

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
   * - ``workspace_path``
     - str | Path | None
     - Root directory for file operations. Defaults to current directory.

Tools Reference
---------------

view_file_outline
~~~~~~~~~~~~~~~~~

Get a structured outline of classes and functions in a file.

.. code-block:: python

   result = await code_tools.view_file_outline(
       file_path="src/utils.py"
   )

**Parameters:**

- ``file_path``: Path to the source file (relative to workspace or absolute)

**Supported file types:** ``.py``, ``.js``, ``.ts``, ``.jsx``, ``.tsx``

**Returns:**

.. code-block:: python

   {
       "success": True,
       "file": "src/utils.py",
       "language": "python",
       "total_lines": 250,
       "symbols": [
           {
               "name": "DataProcessor",
               "kind": "class",
               "start_line": 10,
               "end_line": 85,
               "signature": "class DataProcessor:",
               "docstring": "Processes data from various sources...",
               "children": [
                   {
                       "name": "__init__",
                       "kind": "method",
                       "start_line": 15,
                       "end_line": 25,
                       "signature": "def __init__(self, config: dict):",
                       "docstring": "Initialize processor...",
                       "children": []
                   },
                   {
                       "name": "process",
                       "kind": "method",
                       "start_line": 27,
                       "end_line": 50,
                       "signature": "def process(self, data: list) -> dict:",
                       "docstring": "Process input data...",
                       "children": []
                   }
               ]
           },
           {
               "name": "helper_function",
               "kind": "function",
               "start_line": 90,
               "end_line": 100,
               "signature": "def helper_function(x: int) -> str:",
               "docstring": "A helper function...",
               "children": []
           }
       ]
   }

view_code_item
~~~~~~~~~~~~~~

View the source code of a specific class, function, or method.

.. code-block:: python

   # Get a specific method
   result = await code_tools.view_code_item(
       file_path="src/utils.py",
       node_path="DataProcessor.validate"
   )

   # Get an entire class
   result = await code_tools.view_code_item(
       file_path="src/utils.py",
       node_path="DataProcessor"
   )

   # Get a top-level function
   result = await code_tools.view_code_item(
       file_path="src/utils.py",
       node_path="helper_function"
   )

**Parameters:**

- ``file_path``: Path to the source file
- ``node_path``: Qualified name using dot notation (e.g., ``MyClass.my_method``)

**Returns:**

.. code-block:: python

   {
       "success": True,
       "name": "validate",
       "kind": "method",
       "start_line": 52,
       "end_line": 70,
       "source": "def validate(self, data: dict) -> bool:\n    ..."
   }

Examples
--------

Exploring a Codebase
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import CodeToolSet, FileManagerToolSet

   code_tools = CodeToolSet(name="code", workspace_path="./my_project")
   file_tools = FileManagerToolSet(name="files", path="./my_project")

   explorer = Agent(
       name="code_explorer",
       instructions="""You are a code exploration assistant. When analyzing code:
       1. Use view_file_outline to understand file structure
       2. Use view_code_item to examine specific symbols
       3. Explain the code's purpose and how components interact""",
       model="gpt-4o"
   )
   await explorer.toolset(code_tools)
   await explorer.toolset(file_tools)

   # Explore a file
   result = await explorer.run("Explain the structure of src/main.py")

Code Review Workflow
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # 1. Get file outline
   outline = await code_tools.view_file_outline("api/handlers.py")

   # 2. Review specific functions
   for symbol in outline["symbols"]:
       if symbol["kind"] == "function":
           code = await code_tools.view_code_item(
               "api/handlers.py",
               symbol["name"]
           )
           print(f"Function: {symbol['name']}")
           print(code["source"])

Best Practices
--------------

1. **Start with outlines**: Use ``view_file_outline`` first to understand structure
2. **Drill down selectively**: Only fetch specific symbols you need
3. **Use for large files**: More efficient than reading entire files
4. **Combine with file tools**: Use with FileManagerToolSet for full editing capability

Dependencies
------------

Requires tree-sitter packages:

.. code-block:: bash

   pip install 'pantheon-agents[toolsets]'
