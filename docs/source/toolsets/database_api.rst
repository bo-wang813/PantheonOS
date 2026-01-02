DatabaseAPIQueryToolSet
=======================

The DatabaseAPIQueryToolSet provides LLM-enhanced natural language queries for 26+ biological databases with schema-driven API parameter generation.

Overview
--------

Key features:

* **Natural Language Queries**: Convert natural language to database API calls
* **26+ Databases**: UniProt, PDB, Ensembl, ClinVar, KEGG, and more
* **Schema-Driven**: Uses database schemas for accurate parameter generation
* **Formatted Results**: Returns human-readable results for LLM consumption

Supported Databases
-------------------

**Proteins:**

- UniProt, PDB, AlphaFold, InterPro, STRING, EMDB

**Genomics:**

- Ensembl, ClinVar, dbSNP, GnomAD, GWAS Catalog, UCSC, RegulomeDB

**Expression:**

- GEO, CCRE, OpenTargets, OpenTargets Genetics, ReMap

**Pathways:**

- KEGG, Reactome, GtoPdb

**Specialized:**

- BLAST, JASPAR, MPD, IUCN, PRIDE, cBioPortal, WoRMS, Paleobiology

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import DatabaseAPIQueryToolSet

   # Create database API toolset
   db_tools = DatabaseAPIQueryToolSet(
       name="database_api",
       workspace_path="/path/to/workspace"
   )

   # Create agent and add toolset at runtime
   agent = Agent(
       name="bioinformatician",
       instructions="You can query biological databases using natural language.",
       model="gpt-4o"
   )
   await agent.toolset(db_tools)

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
     - Name of the toolset (default: "database_api")
   * - ``workspace_path``
     - str | None
     - Working directory. Defaults to current directory.

Tools Reference
---------------

query
~~~~~

Query a biological database using natural language.

.. code-block:: python

   result = db_tools.query(
       prompt="Find BRCA1 mutations in breast cancer",
       database="clinvar",
       max_results=5
   )

**Parameters:**

- ``prompt``: Natural language query describing what to find
- ``database``: Target database name (e.g., 'uniprot', 'ensembl', 'clinvar')
- ``max_results``: Maximum number of results to return (default: 5)
- ``llm_service_id``: Optional LLM service ID for parameter generation

**Returns:**

.. code-block:: python

   {
       "success": True,
       "database": "clinvar",
       "prompt": "Find BRCA1 mutations in breast cancer",
       "api_parameters": {"query": "BRCA1[gene] AND breast cancer", ...},
       "raw_count": 150,
       "results": "Found 5 results from clinvar:\n\n1. Entry:\n   ID: ...",
       "strategy": "llm_enhanced"
   }

list_databases
~~~~~~~~~~~~~~

List all available databases with their categories.

.. code-block:: python

   result = db_tools.list_databases()

**Returns:**

.. code-block:: python

   {
       "success": True,
       "databases": ["alphafold", "clinvar", "ensembl", ...],
       "categories": {
           "proteins": ["uniprot", "pdb", "alphafold", ...],
           "genomics": ["ensembl", "clinvar", "dbsnp", ...],
           "expression": ["geo", "ccre", "opentargets", ...],
           "pathways": ["kegg", "reactome", "gtopdb"],
           "specialized": ["blast", "jaspar", "mpd", ...]
       },
       "total": 26
   }

database_info
~~~~~~~~~~~~~

Get detailed information about a specific database.

.. code-block:: python

   result = db_tools.database_info(database="uniprot")

**Returns:**

.. code-block:: python

   {
       "success": True,
       "database": "uniprot",
       "base_url": "https://rest.uniprot.org/uniprotkb",
       "categories": ["search", "entry", "mapping"],
       "example_queries": [
           "Find human insulin protein",
           "Search for p53 tumor suppressor"
       ],
       "is_valid": True
   }

Examples
--------

Protein Research
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Search UniProt for a specific protein
   result = db_tools.query(
       prompt="Find human insulin protein with full sequence",
       database="uniprot",
       max_results=3
   )

   # Get protein structure from PDB
   result = db_tools.query(
       prompt="Find crystal structure of hemoglobin",
       database="pdb",
       max_results=5
   )

Genomics Research
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Search for gene variants
   result = db_tools.query(
       prompt="Find pathogenic variants in CFTR gene",
       database="clinvar",
       max_results=10
   )

   # Get gene information
   result = db_tools.query(
       prompt="Get information about TP53 gene in humans",
       database="ensembl"
   )

Pathway Analysis
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Search KEGG pathways
   result = db_tools.query(
       prompt="Find pathways involved in glycolysis",
       database="kegg",
       max_results=5
   )

   # Search Reactome
   result = db_tools.query(
       prompt="Find signaling pathways involving EGFR",
       database="reactome"
   )

Agent-Driven Research
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import DatabaseAPIQueryToolSet

   db_tools = DatabaseAPIQueryToolSet(name="databases")

   researcher = Agent(
       name="researcher",
       instructions="""You are a bioinformatics researcher. When researching:
       1. Use list_databases to find appropriate databases
       2. Use database_info to understand query options
       3. Use query to search for relevant data
       4. Synthesize findings into comprehensive answers""",
       model="gpt-4o"
   )
   await researcher.toolset(db_tools)

   result = await researcher.run(
       "Research the role of BRCA1 in cancer and find relevant mutations and pathways"
   )

Configuration
-------------

The toolset uses the ``PANTHEON_AGENT_SERVICE_ID`` environment variable for LLM-based parameter generation:

.. code-block:: bash

   export PANTHEON_AGENT_SERVICE_ID="your-service-id"

Best Practices
--------------

1. **Use specific queries**: Include gene names, organisms, and conditions
2. **Check available databases**: Use ``list_databases`` to find appropriate sources
3. **Limit results**: Use ``max_results`` to manage output size
4. **Combine sources**: Query multiple databases for comprehensive research
5. **Review API parameters**: Check ``api_parameters`` in response for transparency

Error Handling
--------------

.. code-block:: python

   result = db_tools.query(
       prompt="Find BRCA1 mutations",
       database="clinvar"
   )

   if result["success"]:
       print(result["results"])
   else:
       print(f"Error: {result['error']}")
       # Check available_databases if database not found
       if "available_databases" in result:
           print(f"Available: {result['available_databases']}")
