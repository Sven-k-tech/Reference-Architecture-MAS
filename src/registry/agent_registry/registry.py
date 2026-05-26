from src.registry.agent_registry.models import AgentInfo
from src.registry.agent_registry.agent_repository import AgentRepository

_repo = AgentRepository()


def register_agent(name: str, capabilities: list[str], llm_config: dict = {}) -> str:
    """Register an agent. Returns the agent_id."""
    agent = AgentInfo(name=name, capabilities=capabilities, llm_config=llm_config)
    _repo.upsert(agent)
    print(f"[Registry] Registered agent '{name}' with id {agent.agent_id}")
    return agent.agent_id

def deregister_agent(agent_id: str):
    """Remove an agent from the registry."""
    _repo.delete(agent_id)
    print(f"[Registry] Deregistered agent {agent_id}")

def list_agents(capability: str = None, status: str = None) -> list[AgentInfo]:
    """View all agents, with optional filtering."""
    return _repo.query(capability=capability, status=status)

def print_registry():
    """Pretty-print all registered agents."""
    agents = _repo.list_all()
    if not agents:
        print("[Registry] No agents registered.")
        return
    print(f"\n{'='*50}")
    print(f"  AGENT REGISTRY  ({len(agents)} agents)")
    print(f"{'='*50}")
    for a in agents:
        caps = ", ".join(a.capabilities) or "none"
        llm  = a.llm_config.get("llm_name", "—")
        print(f"  • {a.name} [{a.status}]")
        print(f"    ID:           {a.agent_id}")
        print(f"    Capabilities: {caps}")
        print(f"    LLM:          {llm}")
        print(f"    Registered:   {a.registered_at:%Y-%m-%d %H:%M:%S}")
        print()
