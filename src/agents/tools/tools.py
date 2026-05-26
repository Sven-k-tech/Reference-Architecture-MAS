from langchain.tools import tool
from tavily import TavilyClient
import arxiv
from src.config.config import get_settings
from src.blackboard.blackboard import Blackboard
import json


# ------------------------------------------------------------------
# Define your Tools here
# ------------------------------------------------------------------

### Your Tool ###





### Taviley Web search tool ###
@tool
def taviley_search_tool(query: str) -> str:
    """
    Search the web for a given query using the Tavily API.
    Args:
        query: The search query string
    Returns titles, URLs, and content snippets for the top results.
    """
    settings = get_settings()
    client = TavilyClient(api_key=settings.taviley_api_key)
    response = client.search(query=query)
    return "\n\n".join(
        f"{r.get('title', '')}\n{r.get('url', '')}\n{r.get('content', '')}"
        for r in response.get("results", [])
    )



### ArXiv search tool ###
@tool
def arxiv_search(query: str) -> str:
    """Search ArXiv for papers matching the query. Returns title, authors, year, URL and abstract for each result."""
    import socket
    print(f"  [Tool] arxiv_search called  |  query: '{query}'")
    try:
        socket.setdefaulttimeout(10)
        client = arxiv.Client(num_retries=1, delay_seconds=1)
        search = arxiv.Search(query=query, max_results=2)
        results = []
        for doc in client.results(search):
            title  = doc.title
            author = ", ".join(a.name for a in doc.authors)
            year   = str(doc.published.year)
            url    = doc.entry_id
            results.append(f"Title: {title}\nAuthor: {author}\nYear: {year}\nURL: {url}\nContent: {doc.summary[:500]}")
    except Exception as e:
        print(f"  [Tool] arxiv_search error: {e}")
        return f"ArXiv search failed: {e}"
    finally:
        socket.setdefaulttimeout(None)
    if not results:
        print("  [Tool] arxiv_search done  |  0 results")
        return "No papers found on ArXiv for this query."
    print(f"  [Tool] arxiv_search done  |  {len(results)} result(s)")
    return "\n---\n".join(results)



### Zotero search tool ###
@tool
def zotero_search(query: str) -> str:
    """Search the Zotero library for papers matching the query. Returns title, author, year and abstract for each result."""
    print(f"  [Tool] zotero_search called  |  query: '{query}'")
    from pyzotero import zotero as pyzotero
    settings = get_settings()
    zot = pyzotero.Zotero(settings.zotero_library_id, "user", settings.zotero_api_key)
    items = zot.items(q=query, limit=5)
    if not items:
        print("  [Tool] zotero_search done  |  0 results")
        return "No items found in Zotero for this query."
    results = []
    for item in items:
        data     = item.get("data", {})
        title    = data.get("title", "N/A")
        year     = data.get("date", "")[:4] or "N/A"
        authors  = ", ".join(
            f"{c.get('lastName', '')} {c.get('firstName', '')}".strip()
            for c in data.get("creators", [])
            if c.get("creatorType") == "author"
        ) or "N/A"
        abstract = data.get("abstractNote", "No abstract available.")[:300]
        results.append(f"Title: {title}\nAuthor: {authors}\nYear: {year}\nAbstract: {abstract}")
    print(f"  [Tool] zotero_search done  |  {len(results)} result(s)")
    return "\n---\n".join(results)



### Blackboard tools ###
@tool
async def read_blackboard(domain: str, key: str) -> str:
    """
    Read a single entry from the shared blackboard.
    Args:
        domain: Knowledge domain (e.g. 'task', 'requirements', 'architecture', 'tests')
        key:    Entry key within that domain (e.g. 'req-001')
    Returns the stored value, or a message if the entry is empty.
    """
    value = await Blackboard().read(domain, key)
    if value is None:
        return f"No entry found at {domain}.{key}."
    return str(value)


@tool
async def read_blackboard_domain(domain: str) -> str:
    """
    Read all entries in a blackboard domain.
    Args:
        domain: Knowledge domain to read (e.g. 'requirements', 'architecture')
    Returns a JSON-formatted dict of all key/value pairs in that domain.
    """
    data = await Blackboard().read(domain)
    if not data:
        return f"Domain '{domain}' is empty."
    return json.dumps(data, indent=2, default=str)


@tool
async def write_blackboard(domain: str, key: str, value: str, agent_id: str) -> str:
    """
    Write a value to a specific domain/key on the shared blackboard.
    Args:
        domain:   Knowledge domain this agent owns (e.g. 'requirements')
        key:      Entry key (e.g. 'req-001')
        value:    The content to store
        agent_id: Name of the agent writing this entry
    """
    entry = await Blackboard().write(domain, key, value, agent_id)
    return f"Written to {domain}.{key} (version {entry.version})."