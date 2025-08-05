Scraper API
===========

The Scraper API toolset provides web scraping capabilities through ScraperAPI, enabling Google search and web page fetching with built-in proxy rotation and anti-bot measures.

Overview
--------

The ``ScraperToolSet`` provides two main tools:

* **google_search**: Perform Google searches via ScraperAPI
* **fetch_web_page**: Fetch and convert web pages to various formats

Key features:

* **Proxy Rotation**: Automatic IP rotation via ScraperAPI
* **Anti-Bot Protection**: Built-in handling of anti-scraping measures
* **Format Conversion**: Output as markdown, HTML, or plain text
* **Concurrent Fetching**: Fetch multiple URLs in parallel
* **Rate Limit Handling**: Automatic retry and rate limit management

Prerequisites
-------------

To use this toolset, you need:

1. A ScraperAPI account and API key
2. Set the environment variable: ``SCRAPER_API_KEY``

Basic Usage
-----------

Setting Up Scraper Toolset
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pantheon.toolsets.scraper import ScraperToolSet
   from pantheon.toolsets.utils.toolset import run_toolsets
   from pantheon.agent import Agent
   
   # Create scraper toolset
   scraper_tools = ScraperToolSet("scraper")
   
   # Run as service
   async with run_toolsets([scraper_tools]):
       # Create agent with scraping capabilities
       agent = Agent(
           name="web_scraper",
           instructions="Search the web and extract information from websites.",
           model="gpt-4.1-mini"
       )
       
       # Connect to scraper toolset
       await agent.remote_toolset(service_name="scraper")

Command Line Deployment
~~~~~~~~~~~~~~~~~~~~~~~

Run the scraper toolset from command line::

    # Set API key
    export SCRAPER_API_KEY=your_api_key_here
    
    # Run toolset
    python -m pantheon.toolsets.scraper --service-name scraper

Google Search
~~~~~~~~~~~~~

.. code-block:: python

   # Perform Google search
   response = await agent.run([{
       "role": "user",
       "content": "Search Google for recent news about artificial intelligence"
   }])
   
   # Agent uses google_search tool with parameters:
   # - query: "recent news about artificial intelligence"
   # - max_results: 10
   # - country: "us"
   # - language: "en"

Web Page Fetching
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Fetch single page
   response = await agent.run([{
       "role": "user",
       "content": "Fetch the content from https://example.com/article"
   }])
   
   # Fetch multiple pages
   response = await agent.run([{
       "role": "user",
       "content": "Fetch content from these 3 URLs and summarize each"
   }])

Tool Parameters
---------------

google_search
~~~~~~~~~~~~~

* ``query`` (str): The search query
* ``max_results`` (int): Maximum number of results (default: 10)
* ``country`` (str): Country code for search (default: "us")
* ``language`` (str): Language code for search (default: "en")
* ``timeout`` (float): Request timeout in seconds (default: 30.0)

fetch_web_page
~~~~~~~~~~~~~~

* ``urls`` (List[str]): List of URLs to fetch
* ``output_format`` (str): Output format - "markdown", "html", or "text" (default: "markdown")
* ``timeout`` (float): Timeout per request in seconds (default: 30.0)

Common Use Cases
----------------

Research Assistant
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   researcher = Agent(
       name="research_assistant",
       instructions="""Research topics by:
       1. Search Google for relevant information
       2. Fetch top results
       3. Extract and summarize key points
       4. Provide sources""",
       model="gpt-4.1"
   )
   
   response = await researcher.run([{
       "role": "user",
       "content": "Research the latest developments in quantum computing"
   }])

News Aggregator
~~~~~~~~~~~~~~~

.. code-block:: python

   news_agent = Agent(
       name="news_aggregator",
       instructions="""Aggregate news on specific topics:
       1. Search for recent news articles
       2. Fetch article content
       3. Summarize key stories
       4. Identify trends""",
       model="gpt-4.1"
   )
   
   # Daily news briefing
   response = await news_agent.run([{
       "role": "user",
       "content": "Create a daily tech news briefing"
   }])

Content Monitor
~~~~~~~~~~~~~~~

.. code-block:: python

   monitor_agent = Agent(
       name="content_monitor",
       instructions="""Monitor web content:
       1. Fetch specified URLs
       2. Compare with previous versions
       3. Identify changes
       4. Alert on significant updates""",
       model="gpt-4.1-mini"
   )
   
   # Monitor competitor websites
   urls_to_monitor = [
       "https://competitor1.com/pricing",
       "https://competitor2.com/features"
   ]

Advanced Patterns
-----------------

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   batch_scraper = Agent(
       name="batch_processor",
       instructions="Process multiple URLs efficiently"
   )
   
   # Process URLs in batches
   urls = ["https://site1.com", "https://site2.com", "https://site3.com"]
   response = await batch_scraper.run([{
       "role": "user",
       "content": f"Fetch and analyze these URLs: {urls}"
   }])

Search and Analyze
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   analyst = Agent(
       name="search_analyst",
       instructions="""For each search:
       1. Search Google for the topic
       2. Fetch top 5 results
       3. Extract key information
       4. Synthesize findings
       5. Provide analysis""",
       model="gpt-4.1"
   )
   
   # Comprehensive analysis
   response = await analyst.run([{
       "role": "user",
       "content": "Analyze market trends for electric vehicles in 2024"
   }])

Multi-Language Support
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   multilingual_agent = Agent(
       name="multilingual_scraper",
       instructions="Search and fetch content in multiple languages"
   )
   
   # Search in different languages/countries
   searches = [
       {"query": "technologie IA", "country": "fr", "language": "fr"},
       {"query": "KI Technologie", "country": "de", "language": "de"},
       {"query": "AI technology", "country": "us", "language": "en"}
   ]

Error Handling
--------------

The toolset includes built-in error handling:

1. **Missing API Key**: Raises ValueError if SCRAPER_API_KEY not set
2. **HTTP Errors**: Logs errors and returns empty content for failed URLs
3. **Timeout Handling**: Configurable timeout with graceful failure
4. **Batch Resilience**: Failed URLs don't stop processing of others

Best Practices
--------------

1. **API Key Security**: Store API key in environment variables, not code
2. **Rate Limiting**: Be mindful of ScraperAPI rate limits
3. **Error Recovery**: Check for empty results and handle gracefully
4. **Batch Efficiency**: Use batch fetching for multiple URLs
5. **Format Selection**: Choose appropriate output format for your needs
6. **Timeout Configuration**: Adjust timeout based on target site responsiveness

Integration Examples
--------------------

With Data Analysis
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Combine with Python toolset for analysis
   data_scraper = Agent(
       name="data_analyst",
       instructions="Scrape web data and analyze with Python"
   )
   await data_scraper.remote_toolset(service_name="scraper")
   await data_scraper.remote_toolset(service_name="python")

With File Storage
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Save scraped content to files
   archiver = Agent(
       name="web_archiver",
       instructions="Scrape and archive web content",
       tools=[write_file]
   )
   await archiver.remote_toolset(service_name="scraper")

Performance Tips
----------------

* Use markdown format for better structure extraction
* Batch URLs to reduce API calls
* Set appropriate timeouts for slow sites
* Cache results when appropriate
* Use country/language parameters for localized results

Limitations
-----------

* Requires valid ScraperAPI subscription
* Subject to ScraperAPI rate limits
* Cannot handle sites requiring authentication
* No JavaScript interaction capabilities
* Limited to ScraperAPI supported features