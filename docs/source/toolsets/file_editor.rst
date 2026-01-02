FileManagerToolSet
==================

The FileManagerToolSet provides agents with file system operations including reading, writing, editing files, and visual inspection of images and PDFs.

Overview
--------

Key capabilities:

* **File Operations**: Read, write, update text files
* **Path Management**: Create directories, delete, move files
* **Search**: Glob patterns and grep content search
* **Visual Inspection**: Analyze images and PDFs with LLM
* **Patch Application**: Apply unified diff or V4A format patches

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import FileManagerToolSet

   # Create toolset with workspace path
   file_tools = FileManagerToolSet(
       name="files",
       path="/path/to/workspace"
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="developer",
       instructions="Help manage files in the workspace.",
       model="gpt-4o"
   )
   await agent.toolset(file_tools)

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
   * - ``path``
     - str | Path | None
     - Working directory path. Defaults to current directory.
   * - ``black_list``
     - list[str] | None
     - List of filenames to ignore

Tools Reference
---------------

read_file
~~~~~~~~~

Read contents of a text file with optional line range.

.. code-block:: python

   result = await file_tools.read_file(
       file_path="src/main.py",
       start_line=10,    # Optional: 1-indexed, inclusive
       end_line=50,      # Optional: 1-indexed, inclusive
       max_chars=5000    # Optional: character limit
   )

**Returns:**

.. code-block:: python

   {
       "success": True,
       "content": "file contents...",
       "total_lines": 100,
       "format": ".py",
       "truncated": False
   }

write_file
~~~~~~~~~~

Create a new file or overwrite existing file.

.. code-block:: python

   result = await file_tools.write_file(
       file_path="output/report.md",
       content="# Report\n...",
       overwrite=True  # Default: True
   )

**Note:** For editing existing files, use ``update_file`` instead.

update_file
~~~~~~~~~~~

Edit an existing file using string replacement.

.. code-block:: python

   result = await file_tools.update_file(
       file_path="config.py",
       old_string="DEBUG = True",
       new_string="DEBUG = False",
       replace_all=False,   # Default: replace first occurrence
       start_line=None,     # Optional: limit search range
       end_line=None
   )

**Returns:**

.. code-block:: python

   {"success": True, "replacements": 1}

manage_path
~~~~~~~~~~~

Unified tool for directory and file path operations.

.. code-block:: python

   # Create directory
   await file_tools.manage_path("create_dir", "src/components")

   # Delete file or directory
   await file_tools.manage_path("delete", "old_file.py")
   await file_tools.manage_path("delete", "old_folder", recursive=True)

   # Move/rename
   await file_tools.manage_path("move", "old.py", new_path="new.py")

**Operations:**

- ``create_dir``: Create directory (parents created automatically)
- ``delete``: Delete file or directory (use ``recursive=True`` for non-empty dirs)
- ``move``: Move or rename file/directory

glob
~~~~

Find files matching glob patterns using ``fd`` (falls back to pathlib).

.. code-block:: python

   result = await file_tools.glob(
       pattern="**/*.py",           # Glob pattern
       path="src",                  # Optional: subdirectory
       respect_git_ignore=True      # Default: True
   )

**Pattern examples:**

- ``*.py`` - Python files in current directory
- ``**/*.py`` - Python files recursively
- ``test_*.py`` - Test files
- ``src/**/*.ts`` - TypeScript files in src/

grep
~~~~

Search file contents using ``ripgrep`` (falls back to Python re).

.. code-block:: python

   result = await file_tools.grep(
       pattern="TODO",              # Regex pattern
       path="src",                  # Optional: directory to search
       file_pattern="*.py",         # Optional: filter by file pattern
       context_lines=2,             # Lines before/after match
       case_sensitive=False,        # Default: case insensitive
       respect_git_ignore=True
   )

**Returns:**

.. code-block:: python

   {
       "success": True,
       "matches": [
           {
               "file": "src/main.py",
               "line_number": 42,
               "line_content": "# TODO: fix this",
               "context_before": [...],
               "context_after": [...]
           }
       ],
       "total_matches": 5,
       "files_matched": 3
   }

apply_patch
~~~~~~~~~~~

Apply patches to files with fuzzy matching support.

**Unified Diff format:**

.. code-block:: python

   await file_tools.apply_patch('''
   --- a/config.py
   +++ b/config.py
   @@ -1,2 +1,2 @@
    DEBUG = True
   -PORT = 8000
   +PORT = 3000
   ''')

**V4A/Codex format:**

.. code-block:: python

   await file_tools.apply_patch('''
   *** Begin Patch
   *** Update File: api.py
   - old_code()
   + new_code()

   *** Create File: utils.py
   + def helper():
   +     pass
   *** End Patch
   ''', fuzzy_threshold=0.8)

**Parameters:**

- ``patch``: Patch content (format auto-detected)
- ``file_path``: Optional explicit file path
- ``fuzzy_threshold``: 0.0-1.0, default 0.5 (0.8 recommended for AI patches)

Visual Inspection Tools
-----------------------

observe_images
~~~~~~~~~~~~~~

Analyze images using LLM vision capabilities.

.. code-block:: python

   result = await file_tools.observe_images(
       question="What objects are in this image?",
       image_paths=["photo1.jpg", "photo2.png"]
   )

observe_pdf_screenshots
~~~~~~~~~~~~~~~~~~~~~~~

Render PDF pages as images and analyze with LLM.

.. code-block:: python

   result = await file_tools.observe_pdf_screenshots(
       question="Summarize the charts on these pages",
       pdf_path="report.pdf",
       page_numbers=[1, 2, 3],  # Optional: defaults to all pages
       dpi=300                   # Optional: default 300
   )

read_pdf
~~~~~~~~

Extract text content from PDF files.

.. code-block:: python

   result = await file_tools.read_pdf("document.pdf")
   # Returns: {"success": True, "content": "Page 1...", "metadata": {...}}

generate_image
~~~~~~~~~~~~~~

Generate images from text descriptions.

.. code-block:: python

   result = await file_tools.generate_image(
       prompt="A sunset over mountains",
       reference_images=["style.png"]  # Optional: for style transfer
   )

Examples
--------

File Editing Workflow
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import FileManagerToolSet

   file_tools = FileManagerToolSet(name="files", path="./project")

   agent = Agent(
       name="editor",
       instructions="""You are a code editor. When editing files:
       1. Use read_file to see current content
       2. Use update_file for small changes
       3. Use apply_patch for multiple changes""",
       model="gpt-4o"
   )
   await agent.toolset(file_tools)

   # The agent will use appropriate tools:
   # - read_file to view code
   # - update_file for single replacements
   # - apply_patch for multi-line changes

Search and Replace
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Find all TODOs
   todos = await file_tools.grep("TODO", file_pattern="**/*.py")

   # Find specific files
   configs = await file_tools.glob("**/config*.yaml")

   # Update found files
   for match in todos["matches"]:
       await file_tools.update_file(
           match["file"],
           old_string="TODO:",
           new_string="DONE:",
           replace_all=True
       )

Best Practices
--------------

1. **Use update_file for edits**: Don't rewrite entire files with ``write_file``
2. **Use apply_patch for multi-file changes**: More efficient and safer
3. **Use glob/grep for search**: More efficient than reading all files
4. **Set fuzzy_threshold for AI patches**: Use 0.8 for tolerant matching
5. **Respect line limits**: Large files are automatically truncated
