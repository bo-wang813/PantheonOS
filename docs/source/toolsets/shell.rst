ShellToolSet
============

The ShellToolSet provides agents with the ability to execute shell commands with automatic session management and timeout support.

Overview
--------

Key features:

* **Command Execution**: Run shell commands with output capture
* **Session Management**: Automatic shell session handling per client
* **Background Execution**: Long-running commands continue in background on timeout
* **Auto-Recovery**: Automatically restarts crashed shells

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import ShellToolSet

   # Create shell toolset
   shell_tools = ShellToolSet(
       name="shell",
       workdir="/path/to/workspace"  # Optional working directory
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="developer",
       instructions="Help run commands and manage processes.",
       model="gpt-4o"
   )
   await agent.toolset(shell_tools)

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
     - Working directory for shell sessions. Defaults to current directory.

Tools Reference
---------------

run_command
~~~~~~~~~~~

Execute a shell command with automatic session management.

.. code-block:: python

   result = await shell_tools.run_command(
       command="ls -la",
       timeout=30,        # Optional: timeout in seconds
       max_output=5000    # Optional: truncate output
   )

**Parameters:**

- ``command``: The command to execute
- ``timeout``: Optional timeout in seconds. On timeout, command continues in background.
- ``shell_id``: Optional. Specify a particular shell session to use.
- ``max_output``: Optional. Max output characters (useful for verbose commands).

**Returns:**

.. code-block:: python

   {
       "success": True,
       "output": "command output...",
       "status": "completed",  # or "timeout"
       "shell_id": "abc123",   # for follow-up on timeout
       "truncated": False
   }

**Timeout Behavior:**

When a command exceeds the timeout, it continues running in the background:

.. code-block:: python

   # Start long-running command
   result = await shell_tools.run_command(
       command="npm run build",
       timeout=10
   )
   # result["status"] == "timeout"
   # result["shell_id"] == "abc123"

   # Later, check progress
   result = await shell_tools.get_shell_output(
       shell_id="abc123",
       timeout=5
   )

get_shell_output
~~~~~~~~~~~~~~~~

Fetch output from a background command (after timeout).

.. code-block:: python

   result = await shell_tools.get_shell_output(
       shell_id="abc123",
       timeout=5,           # How long to wait for output
       max_output=10000     # Optional: truncate long output
   )

**Returns:**

.. code-block:: python

   {
       "success": True,
       "output": "remaining output...",
       "status": "completed",  # or "timeout" if still running
       "shell_id": "abc123",
       "truncated": False
   }

close_shell
~~~~~~~~~~~

Close a specific shell session.

.. code-block:: python

   result = await shell_tools.close_shell(shell_id="abc123")

Session Management
------------------

ShellToolSet automatically manages shell sessions:

- **Auto-allocation**: A shell is created automatically on first command
- **Client isolation**: Each client_id gets its own shell session
- **Busy shell handling**: If current shell is running a background command, a new shell is allocated
- **Auto-recovery**: Crashed shells are automatically restarted

Examples
--------

Basic Commands
~~~~~~~~~~~~~~

.. code-block:: python

   # List files
   await shell_tools.run_command(command="ls -la")

   # Find files
   await shell_tools.run_command(command="find . -name '*.py' | head -20")

   # Check disk usage
   await shell_tools.run_command(command="du -sh *")

Long-Running Commands
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Start build with timeout
   result = await shell_tools.run_command(
       command="npm run build",
       timeout=30
   )

   if result["status"] == "timeout":
       shell_id = result["shell_id"]

       # Check progress periodically
       while True:
           result = await shell_tools.get_shell_output(
               shell_id=shell_id,
               timeout=10
           )
           print(result["output"])

           if result["status"] == "completed":
               break

Verbose Commands
~~~~~~~~~~~~~~~~

For commands with large output, use ``max_output``:

.. code-block:: python

   # Limit output for package installation
   result = await shell_tools.run_command(
       command="pip install tensorflow",
       max_output=5000  # Truncate to ~5000 chars
   )

   # result["truncated"] == True if output was truncated

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Context variables from the agent are automatically exported to the shell:

.. code-block:: python

   # Context variables are available as environment variables
   # e.g., $CONTEXT_VAR_NAME

   result = await shell_tools.run_command(command="echo $HOME")

Best Practices
--------------

1. **Use timeout for long commands**: Prevents blocking on slow operations
2. **Limit output for verbose commands**: Use ``max_output`` to save tokens
3. **Use head/tail for large outputs**: e.g., ``git log -n 5`` instead of ``git log``
4. **Check status on timeout**: Use ``get_shell_output`` to monitor background commands
5. **Run in containers**: The toolset executes arbitrary commands - use isolated environments

Security Warning
----------------

This toolset can execute arbitrary shell commands. Always:

- Run in a sandboxed environment (Docker, VM)
- Limit agent instructions to specific tasks
- Monitor command execution
- Avoid exposing to untrusted input
