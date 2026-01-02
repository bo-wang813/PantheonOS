WebToolSet
==========

The WebToolSet provides web search and content retrieval capabilities through DuckDuckGo search and web crawling using crawl4ai.

Overview
--------

Key features:

* **Web Search**: Search the web using DuckDuckGo (no API key required)
* **Web Crawling**: Fetch and extract content from URLs as markdown
* **Concurrent Fetching**: Fetch multiple URLs in parallel
* **Timeout Support**: Configurable timeouts for reliable operation

Basic Usage
-----------

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import WebToolSet

   # Create web toolset
   web_tools = WebToolSet(name="web")

   # Create agent and add toolset at runtime
   agent = Agent(
       name="researcher",
       instructions="You can search the web and analyze content.",
       model="gpt-4o"
   )
   await agent.toolset(web_tools)

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

Tools Reference
---------------

duckduckgo_search
~~~~~~~~~~~~~~~~~

Search the web using DuckDuckGo.

.. code-block:: python

   results = await web_tools.duckduckgo_search(
       query="machine learning tutorials",
       max_results=10,       # Optional: default 10
       time_limit="w"        # Optional: d/w/m/y for day/week/month/year
   )

**Parameters:**

- ``query``: The search query
- ``max_results``: Maximum number of results (default: 10)
- ``time_limit``: Time filter - "d" (day), "w" (week), "m" (month), "y" (year)

**Returns:**

List of search results with title, href, and body:

.. code-block:: python

   [
       {
           "title": "Introduction to Machine Learning",
           "href": "https://example.com/ml-intro",
           "body": "A comprehensive guide to..."
       },
       ...
   ]

web_crawl
~~~~~~~~~

Fetch and extract content from URLs as markdown.

.. code-block:: python

   contents = await web_tools.web_crawl(
       urls=["https://example.com/page1", "https://example.com/page2"],
       timeout=20.0          # Optional: default 20 seconds
   )

**Parameters:**

- ``urls``: List of URLs to crawl
- ``timeout``: Request timeout in seconds (default: 20.0)

**Returns:**

List of markdown content from each URL:

.. code-block:: python

   [
       "# Page 1 Title\n\nContent from page 1...",
       "# Page 2 Title\n\nContent from page 2...",
   ]

Examples
--------

Research Workflow
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon import Agent
   from pantheon.toolsets import WebToolSet

   web_tools = WebToolSet(name="web")

   research_agent = Agent(
       name="researcher",
       instructions="""Conduct thorough research:
       1. Search for multiple sources
       2. Visit relevant links
       3. Extract and synthesize information
       4. Provide comprehensive analysis with citations""",
       model="gpt-4o"
   )
   await research_agent.toolset(web_tools)

   result = await research_agent.run(
       "Research the impact of AI on healthcare with at least 3 sources"
   )

News Monitoring
~~~~~~~~~~~~~~~

.. code-block:: python

   news_agent = Agent(
       name="news_monitor",
       instructions="""Monitor news on specific topics:
       1. Search for recent news using time_limit
       2. Fetch full articles
       3. Summarize key developments""",
       model="gpt-4o"
   )
   await news_agent.toolset(web_tools)

   # Find news from the past week
   result = await news_agent.run(
       "Find news about renewable energy from the past week"
   )

Content Extraction
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Fetch multiple pages concurrently
   contents = await web_tools.web_crawl(
       urls=[
           "https://docs.python.org/3/tutorial/",
           "https://numpy.org/doc/stable/user/",
           "https://pandas.pydata.org/docs/getting_started/"
       ],
       timeout=30.0
   )

   # contents[0] = Python tutorial markdown
   # contents[1] = NumPy docs markdown
   # contents[2] = Pandas docs markdown

Best Practices
--------------

1. **Use time_limit for recent content**: Filter results by recency
2. **Batch URL fetches**: Use web_crawl with multiple URLs for efficiency
3. **Set appropriate timeouts**: Longer for complex pages
4. **Verify sources**: Cross-reference information from multiple sources
5. **Handle empty results**: Some pages may fail to load

Limitations
-----------

- JavaScript-heavy sites may not render fully (uses crawl4ai)
- Some sites block automated access
- Rate limits may apply to DuckDuckGo
- Cannot handle authentication-required pages
- Limited to publicly accessible content
