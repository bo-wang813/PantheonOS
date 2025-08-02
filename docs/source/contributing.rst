Contributing
============

We welcome contributions to Pantheon Agents! This guide will help you get started.

Getting Started
---------------

1. **Fork the Repository**

   Visit https://github.com/your-org/pantheon-agents and click "Fork"

2. **Clone Your Fork**

   .. code-block:: bash

      git clone https://github.com/YOUR_USERNAME/pantheon-agents.git
      cd pantheon-agents

3. **Set Up Development Environment**

   .. code-block:: bash

      # Create conda environment
      conda create -n pantheon-dev python=3.9
      conda activate pantheon-dev
      
      # Install in development mode
      pip install -e ".[dev]"
      
      # Install pre-commit hooks
      pre-commit install

Development Workflow
--------------------

1. **Create a Branch**

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Make Your Changes**

   - Write code following our style guide
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Tests**

   .. code-block:: bash

      # Run all tests
      pytest
      
      # Run specific tests
      pytest tests/test_agent.py
      
      # Run with coverage
      pytest --cov=pantheon

4. **Format and Lint**

   .. code-block:: bash

      # Format code
      black pantheon/
      isort pantheon/
      
      # Run linters
      flake8 pantheon/
      mypy pantheon/

5. **Commit Your Changes**

   .. code-block:: bash

      git add .
      git commit -m "feat: add new feature"
      
      # We follow conventional commits:
      # feat: new feature
      # fix: bug fix
      # docs: documentation changes
      # style: formatting changes
      # refactor: code restructuring
      # test: test additions/changes
      # chore: maintenance tasks

6. **Push and Create PR**

   .. code-block:: bash

      git push origin feature/your-feature-name

   Then create a Pull Request on GitHub.

Code Style Guide
----------------

Python Code
~~~~~~~~~~~

We follow PEP 8 with these additions:

- Line length: 88 characters (Black default)
- Use type hints for all public functions
- Docstrings in Google style

.. code-block:: python

   from typing import List, Optional
   
   async def process_data(
       data: List[str],
       validate: bool = True,
       timeout: Optional[float] = None
   ) -> ProcessResult:
       """Process a list of data items.
       
       Args:
           data: List of strings to process
           validate: Whether to validate input data
           timeout: Optional timeout in seconds
           
       Returns:
           ProcessResult object containing results
           
       Raises:
           ValueError: If data is invalid
           TimeoutError: If processing exceeds timeout
       """
       # Implementation here
       pass

Documentation
~~~~~~~~~~~~~

- Use clear, concise language
- Include code examples
- Update relevant guides
- Add docstrings to all public APIs

Testing Guidelines
------------------

Test Structure
~~~~~~~~~~~~~~

.. code-block:: python

   import pytest
   from pantheon import Agent
   
   class TestAgent:
       """Test cases for Agent class."""
       
       @pytest.fixture
       def agent(self):
           """Create a test agent."""
           return Agent(
               name="TestAgent",
               instructions="Test instructions"
           )
       
       async def test_execute_simple_task(self, agent):
           """Test simple task execution."""
           response = await agent.execute("Hello")
           assert response.success
           assert response.content
       
       async def test_error_handling(self, agent):
           """Test error handling."""
           with pytest.raises(AgentError):
               await agent.execute(None)

Test Coverage
~~~~~~~~~~~~~

- Aim for >90% code coverage
- Test edge cases and error conditions
- Include integration tests
- Add performance tests for critical paths

Pull Request Guidelines
-----------------------

PR Requirements
~~~~~~~~~~~~~~~

1. **Clear Description**: Explain what and why
2. **Tests**: All new code must have tests
3. **Documentation**: Update docs as needed
4. **Changelog**: Add entry to CHANGELOG.md
5. **Clean History**: Squash commits if needed

PR Template
~~~~~~~~~~~

.. code-block:: markdown

   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Tests added/updated
   - [ ] All tests pass
   - [ ] Coverage maintained/increased
   
   ## Checklist
   - [ ] Code follows style guide
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Changelog updated

Areas for Contribution
----------------------

Code Contributions
~~~~~~~~~~~~~~~~~~

- **New Tools**: Extend agent capabilities
- **Team Patterns**: New collaboration strategies
- **Memory Systems**: Alternative storage backends
- **Performance**: Optimization and scaling
- **Bug Fixes**: Issue resolution

Documentation
~~~~~~~~~~~~~

- **Tutorials**: Step-by-step guides
- **Examples**: Real-world use cases
- **API Docs**: Improve clarity
- **Translations**: Internationalization

Community
~~~~~~~~~

- **Issue Triage**: Help categorize issues
- **Code Review**: Review pull requests
- **Support**: Help in discussions
- **Testing**: Test pre-releases

Development Setup
-----------------

Full Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Clone repository
   git clone https://github.com/your-org/pantheon-agents.git
   cd pantheon-agents
   
   # Create conda environment
   conda create -n pantheon-dev python=3.9
   conda activate pantheon-dev
   
   # Install all dependencies
   pip install -e ".[dev,docs,test]"
   
   # Install pre-commit hooks
   pre-commit install
   
   # Set up test database
   python scripts/setup_test_db.py
   
   # Run initial tests
   pytest

Tools and Scripts
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run full test suite
   ./scripts/test.sh
   
   # Format all code
   ./scripts/format.sh
   
   # Build documentation
   ./scripts/build_docs.sh
   
   # Release preparation
   ./scripts/prepare_release.sh

Release Process
---------------

For maintainers:

1. Update version in ``setup.py``
2. Update CHANGELOG.md
3. Create release PR
4. After merge, tag release
5. Build and publish to PyPI

Questions?
----------

- **Discord**: Join our community server
- **GitHub Issues**: For bugs and features
- **Discussions**: For questions and ideas
- **Email**: maintainers@pantheon-agents.org

Thank you for contributing to Pantheon Agents!