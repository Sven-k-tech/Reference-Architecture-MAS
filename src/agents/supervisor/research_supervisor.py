from typing import TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, StateGraph
from src.agents.prompts.prompts import RESEARCH_SUMMARY_PROMPT
from src.config.config import get_llm
from src.agents.experts.researcher import ResearcherAgent
from src.agents.experts.librarian import LibrarianAgent
from src.registry.agent_registry.agent_repository import AgentRepository





# ------------------------------------------------------------------
# Define the State of your Supervisor Graph
# ------------------------------------------------------------------
class SupervisorState(TypedDict):
    research_topic:    str
    registered_agents: list[dict]
    papers_library:    str
    papers_new:        str
    final_summary:     str


# ------------------------------------------------------------------
# Configure your Supervisor with get_llm
# ------------------------------------------------------------------
supervisor_llm = get_llm("groq", "llama-3.3-70b-versatile", 0.2)


# ------------------------------------------------------------------
# Define the Nodes of your Supervisor graph
# ------------------------------------------------------------------
def check_registry_node(state: SupervisorState) -> dict:
    """Query the AgentRegistry and print all registered agents."""
    print("\n[Node] check_registry_node started")
    agents = AgentRepository().list_all()
    print("\n=== Registered Agents ===")
    for a in agents:
        caps = ", ".join(a.capabilities) or "none"
        llm  = a.llm_config.get("llm_name", "—")
        print(f"  • {a.name}  |  capabilities: {caps}  |  LLM: {llm}")
    print("[Node] check_registry_node finished\n")
    return {"registered_agents": [a.model_dump() for a in agents]}


def call_librarian_node(state: SupervisorState, config: RunnableConfig) -> dict:
    """Invoke the LibrarianAgent to search the Zotero library."""
    print("[Node] call_librarian_node started")
    callbacks = config.get("callbacks", [])
    librarian = LibrarianAgent()
    result = librarian.invoke(state["research_topic"], callbacks=callbacks)
    print("[Node] call_librarian_node finished\n")
    return {"papers_library": result}


def call_researcher_node(state: SupervisorState, config: RunnableConfig) -> dict:
    """Invoke the ResearcherAgent to retrieve new papers from ArXiv."""
    print("[Node] call_researcher_node started")
    callbacks = config.get("callbacks", [])
    researcher = ResearcherAgent()
    result = researcher.invoke(state["research_topic"], callbacks=callbacks)
    print("[Node] call_researcher_node finished\n")
    return {"papers_new": result}


def summarize_research_node(state: SupervisorState, config: RunnableConfig) -> dict:
    """Call the supervisor LLM to produce a structured research report and print it."""
    print("[Node] summarize_research_node started")
    callbacks = config.get("callbacks", [])
    messages = [
        SystemMessage(content=RESEARCH_SUMMARY_PROMPT),
        HumanMessage(content=(
            f"Research Topic: {state['research_topic']}\n\n"
            f"=== Existing Literature (Zotero) ===\n{state['papers_library']}\n\n"
            f"=== New Papers (ArXiv) ===\n{state['papers_new']}"
        )),
    ]
    response = supervisor_llm.invoke(messages, config={"callbacks": callbacks})
    print("[Node] summarize_research_node finished\n")
    print("\n=== Research Summary ===")
    print(response.content)
    return {"final_summary": response.content}


# ------------------------------------------------------------------
# Build your Supervisor Graph
# ------------------------------------------------------------------
research_supervisor_builder = StateGraph(SupervisorState)


# ------------------------------------------------------------------
# Add your Supervisor Graph Nodes
# ------------------------------------------------------------------
research_supervisor_builder.add_node("check_registry_node",     check_registry_node)
research_supervisor_builder.add_node("call_librarian_node",     call_librarian_node)
research_supervisor_builder.add_node("call_researcher_node",    call_researcher_node)
research_supervisor_builder.add_node("summarize_research_node", summarize_research_node)


# ------------------------------------------------------------------
# Connect your Supervisor Graph Nodes
# ------------------------------------------------------------------
research_supervisor_builder.add_edge(START,                      "check_registry_node")
research_supervisor_builder.add_edge("check_registry_node",      "call_librarian_node")
research_supervisor_builder.add_edge("call_librarian_node",      "call_researcher_node")
research_supervisor_builder.add_edge("call_researcher_node",     "summarize_research_node")
research_supervisor_builder.add_edge("summarize_research_node",  END)


# ------------------------------------------------------------------
# Compile your Supervisor Graph
# ------------------------------------------------------------------
research_supervisor = research_supervisor_builder.compile()
