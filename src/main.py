from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from src.agents.experts.researcher import ResearcherAgent
from src.agents.experts.librarian  import LibrarianAgent
from src.agents.supervisor.research_supervisor import research_supervisor
from src.observability.observer import get_handler


#-----------------------------------------------------------------------------
# Instantiate expert agents — triggers registration in AgentRegistry and Blackboard
#-----------------------------------------------------------------------------
researcher = ResearcherAgent()
librarian = LibrarianAgent()

# Single Langfuse handler for the full run — creates one unified trace
handler = get_handler()


#-----------------------------------------------------------------------------
# TEST: Invoke LibrarianAgent directly with a research topic
#-----------------------------------------------------------------------------

# RESEARCH_TOPIC = "Tool Squatting"

# print("=" * 60)
# print(f"[TEST] Invoking LibrarianAgent with topic: '{RESEARCH_TOPIC}'")
# print("=" * 60)

# result = librarian.invoke(RESEARCH_TOPIC, callbacks=[handler])

# print("\n[TEST] Librarian result:")
# print(result)
# print("=" * 60)


#-----------------------------------------------------------------------------
# TEST: Test your Expert Agent here, by invoking it.
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Invoke your Supervisor Agent with the initial State. 
# Change the Research Supervisor to Your Supervisor
#-----------------------------------------------------------------------------

research_supervisor.invoke(
    {
        "research_topic":    "Tool Squatting",
        "registered_agents": [],
        "papers_library":    "",
        "papers_new":        "",
        "final_summary":     "",
    },
    config={"callbacks": [handler]},
)
