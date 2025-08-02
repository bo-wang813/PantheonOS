Installation
============

This guide will help you install Pantheon Agents and set up your development environment.

Requirements
------------

- Python 3.8 or higher
- pip package manager
- conda (recommended for environment management)
- Git

Basic Installation
------------------

Install from PyPI
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install pantheon-agents

Install from Source
~~~~~~~~~~~~~~~~~~~

For the latest development version:

.. code-block:: bash

   git clone https://github.com/your-org/pantheon-agents.git
   cd pantheon-agents
   pip install -e .

Development Installation
------------------------

If you're planning to contribute or need development tools:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/your-org/pantheon-agents.git
   cd pantheon-agents

   # Create conda environment
   conda create -n pantheon python=3.9
   conda activate pantheon

   # Install with development dependencies
   pip install -e ".[dev]"

Environment Setup
-----------------

API Keys
~~~~~~~~

Pantheon Agents requires API keys for LLM providers:

.. code-block:: bash

   # OpenAI
   export OPENAI_API_KEY="your-openai-api-key"

   # Anthropic (optional)
   export ANTHROPIC_API_KEY="your-anthropic-api-key"

   # Google (optional)
   export GOOGLE_API_KEY="your-google-api-key"

Configuration File
~~~~~~~~~~~~~~~~~~

Create a configuration file at ``~/.pantheon/config.yaml``:

.. code-block:: yaml

   # Default LLM provider
   default_provider: openai
   
   # Model settings
   models:
     openai:
       model: gpt-4
       temperature: 0.7
     anthropic:
       model: claude-3-opus-20240229
       temperature: 0.7
   
   # Memory settings
   memory:
     storage_path: ~/.pantheon/memory
     max_history: 100
   
   # Tool settings
   tools:
     python:
       timeout: 300
     shell:
       allowed_commands:
         - ls
         - cat
         - grep
         - find

Verify Installation
-------------------

To verify your installation:

.. code-block:: python

   import pantheon
   from pantheon import Agent

   # Check version
   print(pantheon.__version__)

   # Create a simple agent
   agent = Agent(
       name="TestAgent",
       instructions="You are a helpful assistant"
   )

   # Test the agent
   response = await agent.execute("Hello!")
   print(response)

Docker Installation
-------------------

For containerized deployment:

.. code-block:: dockerfile

   FROM python:3.9-slim

   WORKDIR /app

   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       git \
       build-essential \
       && rm -rf /var/lib/apt/lists/*

   # Install Pantheon Agents
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   RUN pip install pantheon-agents

   # Copy application code
   COPY . .

   # Set environment variables
   ENV PYTHONUNBUFFERED=1

   CMD ["python", "-m", "pantheon.chatroom"]

Build and run:

.. code-block:: bash

   docker build -t pantheon-agents .
   docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8000:8000 pantheon-agents

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Import Error**: "No module named 'pantheon'"
   Make sure you've activated the correct conda environment:
   
   .. code-block:: bash
   
      conda activate pantheon

**API Key Error**: "OpenAI API key not found"
   Ensure your API key is set:
   
   .. code-block:: bash
   
      echo $OPENAI_API_KEY  # Should show your key
      export OPENAI_API_KEY="sk-..."

**Permission Error**: When accessing memory files
   Check permissions on the memory directory:
   
   .. code-block:: bash
   
      chmod -R 755 ~/.pantheon/memory

Next Steps
----------

After installation, proceed to:

- :doc:`quickstart` - Learn the basics
- :doc:`concepts` - Understand core concepts
- :doc:`guides/agents` - Create your first agent