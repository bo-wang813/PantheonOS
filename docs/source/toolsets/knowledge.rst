KnowledgeToolSet
================

The KnowledgeToolSet provides comprehensive knowledge base management with hybrid retrieval (vector + BM25 + reranking) using Qdrant.

Overview
--------

Key features:

* **Collection Management**: Create, list, and delete knowledge collections
* **Source Management**: Add files, folders, or URLs to collections
* **Hybrid Retrieval**: Vector + BM25 + FlashRank reranking
* **Metadata Extraction**: Optional title, keyword, and summary extraction via LLM
* **Chat Configuration**: Per-session active collections and auto-search settings
* **Async Processing**: Background document indexing with progress tracking

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import KnowledgeToolSet

   # Create knowledge toolset
   knowledge_tools = KnowledgeToolSet(
       name="knowledge",
       config_path="path/to/config.json"  # Optional
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="researcher",
       instructions="You can search and manage knowledge bases.",
       model="gpt-4o"
   )
   await agent.toolset(knowledge_tools)

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
     - Name of the toolset (default: "knowledge")
   * - ``config_path``
     - str | None
     - Path to configuration file. Uses default settings if not provided.

Tools Reference
---------------

search_knowledge
~~~~~~~~~~~~~~~~

Search the knowledge base with hybrid retrieval.

.. code-block:: python

   result = await knowledge_tools.search_knowledge(
       query="What is machine learning?",
       top_k=5,                    # Number of results
       collection_ids=None,        # Use session's active collections
       use_hybrid=True             # Enable hybrid retrieval
   )

**Parameters:**

- ``query``: Search query text
- ``top_k``: Number of results to return (default: 5)
- ``collection_ids``: Optional list of collection IDs. Uses session's active collections if not specified.
- ``use_hybrid``: Whether to use hybrid retrieval (default: True)

**Returns:**

.. code-block:: python

   {
       "success": True,
       "results": [
           {
               "id": "node_abc123",
               "text": "Machine learning is...",
               "metadata": {"source_name": "ml_intro.pdf", ...},
               "score": 0.95,
               "collection_id": "col_xyz789"
           }
       ],
       "searched_collections": ["col_xyz789"]
   }

Collection Management (Internal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These methods are marked ``exclude=True`` and used by UI/API:

**list_collections**

.. code-block:: python

   result = await knowledge_tools.list_collections()
   # Returns: {"success": True, "collections": [...], "total": 5}

**create_collection**

.. code-block:: python

   result = await knowledge_tools.create_collection(
       name="Research Papers",
       description="Academic papers collection"
   )
   # Returns: {"success": True, "collection": {...}}

**delete_collection**

.. code-block:: python

   result = await knowledge_tools.delete_collection(
       collection_id="col_abc123"
   )
   # Returns: {"success": True}

Source Management (Internal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**add_sources**

.. code-block:: python

   # Add single source
   result = await knowledge_tools.add_sources(
       collection_id="col_abc123",
       sources={"type": "file", "path": "/path/to/doc.pdf"}
   )

   # Add multiple sources
   result = await knowledge_tools.add_sources(
       collection_id="col_abc123",
       sources=[
           {"type": "file", "path": "/path/to/doc1.pdf"},
           {"type": "folder", "path": "/path/to/docs/"},
       ]
   )
   # Returns: {"success": True, "source_ids": [...], "message": "..."}

**Source types:**

- ``file``: Single file (PDF, TXT, MD, DOCX, etc.)
- ``folder``: Directory with documents (recursive scan)
- ``url``: Web URL (not yet implemented)

**list_sources**

.. code-block:: python

   result = await knowledge_tools.list_sources(
       collection_id="col_abc123"
   )
   # Returns: {"success": True, "sources": [...], "total": 3}

**remove_source**

.. code-block:: python

   result = await knowledge_tools.remove_source(
       collection_id="col_abc123",
       source_id="src_xyz789"
   )
   # Returns: {"success": True}

Chat Configuration (Internal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**get_chat_knowledge**

.. code-block:: python

   result = await knowledge_tools.get_chat_knowledge()
   # Returns current session's knowledge config

**enable_collection / disable_collection**

.. code-block:: python

   await knowledge_tools.enable_collection(collection_id="col_abc123")
   await knowledge_tools.disable_collection(collection_id="col_abc123")

**set_auto_search**

.. code-block:: python

   await knowledge_tools.set_auto_search(enabled=True)

Configuration
-------------

The toolset uses a configuration file with the following structure:

.. code-block:: json

   {
     "knowledge": {
       "embedding": {
         "model": "text-embedding-3-small"
       },
       "chunking": {
         "chunk_size": 512,
         "chunk_overlap": 50
       },
       "retrieval": {
         "use_reranker": true,
         "hybrid_alpha": 0.5
       },
       "metadata": {
         "path": ".pantheon/knowledge/metadata.json",
         "extract_title": false,
         "extract_keywords": false,
         "extract_summary": false
       }
     }
   }

Architecture
------------

The toolset uses a multi-layer architecture:

1. **KnowledgeToolSet**: Tool interface and metadata management
2. **VectorStoreBackend**: Qdrant-based vector storage with hybrid search
3. **LlamaIndex**: Document loading, chunking, and metadata extraction

**Retrieval Pipeline:**

1. Query → Dense + Sparse embeddings
2. Qdrant hybrid search (vector + BM25)
3. FlashRank reranking
4. Results returned with metadata

Examples
--------

Building a Research Assistant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import KnowledgeToolSet, FileManagerToolSet

   knowledge_tools = KnowledgeToolSet(name="knowledge")
   file_tools = FileManagerToolSet(name="files")

   researcher = Agent(
       name="researcher",
       instructions="""You are a research assistant. When asked questions:
       1. Search the knowledge base for relevant information
       2. Synthesize findings into a comprehensive answer
       3. Cite sources from the search results""",
       model="gpt-4o"
   )
   await researcher.toolset(knowledge_tools)
   await researcher.toolset(file_tools)

   result = await researcher.run(
       "What are the key findings about neural networks?"
   )

Best Practices
--------------

1. **Use collections for organization**: Group related documents together
2. **Enable hybrid retrieval**: Combines semantic and keyword matching
3. **Monitor indexing status**: Check source status after adding
4. **Use appropriate chunk sizes**: 256-512 tokens for most use cases
5. **Enable reranking**: Improves result quality significantly

Dependencies
------------

Requires additional packages:

.. code-block:: bash

   pip install qdrant-client llama-index fastembed
