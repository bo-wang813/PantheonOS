Examples and Tutorials
======================

Learn by example with these practical demonstrations of Pantheon Agents capabilities.

Getting Started Examples
------------------------

.. grid:: 1 1 2 2
   :gutter: 3

   .. grid-item-card:: 🎯 Basic Agent
      :link: basic_agent
      :link-type: doc

      Create your first agent and execute simple tasks.

   .. grid-item-card:: 👥 Team Collaboration
      :link: team_collaboration
      :link-type: doc

      Build teams of agents working together on complex tasks.

   .. grid-item-card:: 🛠️ Custom Tools
      :link: custom_tools
      :link-type: doc

      Extend agent capabilities with custom tool implementations.

   .. grid-item-card:: 🌐 Distributed Setup
      :link: distributed_setup
      :link-type: doc

      Deploy agents across multiple machines for scalability.

By Use Case
-----------

Development & DevOps
~~~~~~~~~~~~~~~~~~~~

**Code Review System**
   Multi-agent system for automated code review:
   
   .. code-block:: python
   
      reviewer = Agent("Reviewer", tools=[GitTools()])
      tester = Agent("Tester", tools=[PythonTools()])
      security = Agent("Security", tools=[SecurityTools()])
      
      review_team = Team([reviewer, tester, security])

**CI/CD Pipeline**
   Automated deployment pipeline with agents:
   
   .. code-block:: python
   
      builder = Agent("Builder", tools=[DockerTools()])
      tester = Agent("Tester", tools=[TestTools()])
      deployer = Agent("Deployer", tools=[K8sTools()])

Data Science & Analytics
~~~~~~~~~~~~~~~~~~~~~~~~

**Data Pipeline**
   ETL pipeline with specialized agents:
   
   .. code-block:: python
   
      extractor = Agent("Extractor", tools=[DatabaseTools()])
      transformer = Agent("Transformer", tools=[PandasTools()])
      analyzer = Agent("Analyzer", tools=[StatsTools()])

**ML Model Development**
   Collaborative model building:
   
   .. code-block:: python
   
      data_prep = Agent("DataPrep", tools=[PandasTools()])
      modeler = Agent("Modeler", tools=[SKLearnTools()])
      evaluator = Agent("Evaluator", tools=[MLTools()])

Research & Analysis
~~~~~~~~~~~~~~~~~~~

**Market Research**
   Comprehensive research system:
   
   .. code-block:: python
   
      web_researcher = Agent("WebExpert", tools=[WebTools()])
      data_analyst = Agent("Analyst", tools=[PythonTools()])
      report_writer = Agent("Writer", tools=[DocTools()])

**Academic Research**
   Literature review and analysis:
   
   .. code-block:: python
   
      scholar = Agent("Scholar", tools=[ScholarTools()])
      synthesizer = Agent("Synthesizer")
      critic = Agent("Critic")

Business Applications
~~~~~~~~~~~~~~~~~~~~~

**Customer Support**
   Intelligent support system:
   
   .. code-block:: python
   
      classifier = Agent("Classifier")
      tech_support = Agent("TechSupport", tools=[KBTools()])
      escalation = Agent("Escalation")

**Content Creation**
   Multi-format content generation:
   
   .. code-block:: python
   
      researcher = Agent("Researcher", tools=[WebTools()])
      writer = Agent("Writer")
      editor = Agent("Editor")
      publisher = Agent("Publisher", tools=[CMSTools()])

Complete Examples
-----------------

Each example includes:

- **Objective**: What the example demonstrates
- **Prerequisites**: Required setup and dependencies
- **Code**: Complete, runnable implementation
- **Explanation**: Step-by-step walkthrough
- **Extensions**: Ideas for expanding the example

Example Structure
~~~~~~~~~~~~~~~~~

.. code-block:: python

   """
   Example: Multi-Agent Research System
   
   This example demonstrates how to build a research system
   that gathers information from multiple sources and creates
   comprehensive reports.
   """
   
   import asyncio
   from pantheon import Agent, Team
   from pantheon.tools import WebTools, PythonTools, FileTools
   
   async def main():
       # 1. Create specialized agents
       # 2. Configure team collaboration
       # 3. Execute research task
       # 4. Process and present results
       pass
   
   if __name__ == "__main__":
       asyncio.run(main())

Running Examples
----------------

1. **Clone Repository**

   .. code-block:: bash
   
      git clone https://github.com/your-org/pantheon-agents
      cd pantheon-agents/examples

2. **Install Dependencies**

   .. code-block:: bash
   
      pip install pantheon-agents
      pip install -r requirements.txt

3. **Set API Keys**

   .. code-block:: bash
   
      export OPENAI_API_KEY="your-key"

4. **Run Example**

   .. code-block:: bash
   
      python basic_agent_example.py

Interactive Notebooks
---------------------

Jupyter notebooks for interactive learning:

- ``01_getting_started.ipynb`` - Introduction to agents
- ``02_tools_and_memory.ipynb`` - Using tools and memory
- ``03_team_patterns.ipynb`` - Team collaboration patterns
- ``04_advanced_features.ipynb`` - Advanced configurations
- ``05_distributed_systems.ipynb`` - Multi-machine setups

Contributing Examples
---------------------

We welcome example contributions! Guidelines:

1. **Clear Purpose**: Example should demonstrate specific features
2. **Self-Contained**: Minimal external dependencies
3. **Well-Documented**: Include comments and docstrings
4. **Tested**: Ensure example runs without errors
5. **Practical**: Show real-world use cases

Submit examples via pull request to the `examples/` directory.

.. toctree::
   :hidden:
   :maxdepth: 2

   basic_agent
   team_collaboration
   custom_tools
   distributed_setup
   code_review_system
   data_pipeline
   research_system
   support_bot