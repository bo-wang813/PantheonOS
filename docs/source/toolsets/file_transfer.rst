FileTransferToolSet
===================

The FileTransferToolSet provides file transfer capabilities with chunked I/O support for streaming file uploads and base64-encoded file reading.

Overview
--------

Key features:

* **Chunked Upload**: Stream large files in chunks
* **Handle-Based Access**: Open, write, close pattern for uploads
* **Base64 Reading**: JSON-compatible file content transfer
* **Security**: Path traversal protection

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import FileTransferToolSet

   # Create file transfer toolset
   transfer_tools = FileTransferToolSet(
       name="transfer",
       path="/path/to/workspace"
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="file_handler",
       instructions="You can transfer files.",
       model="gpt-4o"
   )
   await agent.toolset(transfer_tools)

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
     - str | Path
     - Base directory for file operations

Tools Reference
---------------

open_file_for_write
~~~~~~~~~~~~~~~~~~~

Open a file for writing and get a handle ID.

.. code-block:: python

   result = await transfer_tools.open_file_for_write(
       file_path="uploads/data.bin"
   )

**Returns:**

.. code-block:: python

   {"success": True, "handle_id": "abc123-uuid"}

write_chunk
~~~~~~~~~~~

Write a chunk of data to an open file.

.. code-block:: python

   result = await transfer_tools.write_chunk(
       handle_id="abc123-uuid",
       data=b"binary data chunk"
   )

**Returns:**

.. code-block:: python

   {"success": True}

close_file
~~~~~~~~~~

Close an open file handle.

.. code-block:: python

   result = await transfer_tools.close_file(
       handle_id="abc123-uuid"
   )

**Returns:**

.. code-block:: python

   {"success": True}

read_file
~~~~~~~~~

Read a file and return its contents.

.. code-block:: python

   # Non-streaming mode (returns base64)
   result = await transfer_tools.read_file(
       file_path="data/file.bin"
   )

**Returns:**

.. code-block:: python

   {
       "success": True,
       "data": "base64EncodedContent...",
       "total_size": 1024,
       "encoding": "base64"
   }

Examples
--------

Uploading a Large File
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import base64

   async def upload_file(transfer_tools, source_path, dest_path):
       # Open file for writing
       result = await transfer_tools.open_file_for_write(dest_path)
       if not result["success"]:
           return result

       handle_id = result["handle_id"]

       try:
           # Read source in chunks and write
           with open(source_path, "rb") as f:
               while True:
                   chunk = f.read(1024 * 64)  # 64KB chunks
                   if not chunk:
                       break
                   await transfer_tools.write_chunk(handle_id, chunk)
       finally:
           # Always close the handle
           await transfer_tools.close_file(handle_id)

       return {"success": True}

Downloading a File
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import base64

   async def download_file(transfer_tools, remote_path, local_path):
       result = await transfer_tools.read_file(remote_path)
       if not result["success"]:
           return result

       # Decode base64 and save
       data = base64.b64decode(result["data"])
       with open(local_path, "wb") as f:
           f.write(data)

       return {"success": True, "size": len(data)}

Security
--------

The toolset includes path traversal protection:

.. code-block:: python

   # This will fail - ".." not allowed
   result = await transfer_tools.open_file_for_write("../outside.txt")
   # Returns: {"error": "File path cannot contain '..'"}

Best Practices
--------------

1. **Always close handles**: Use try/finally to ensure handles are closed
2. **Use appropriate chunk sizes**: 64KB is a good default for most use cases
3. **Check success status**: Always check the ``success`` field in responses
4. **Handle base64 encoding**: Remember to decode when reading files
