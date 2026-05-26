from src.registry.agent_registry.models import AgentInfo
from threading import Lock
from datetime import datetime

class AgentRepository:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._store = {}
            cls._instance._lock = Lock()
        return cls._instance

    def upsert(self, agent: AgentInfo) -> AgentInfo:
        with self._lock:
            agent.last_seen = datetime.utcnow()
            self._store[agent.agent_id] = agent
            return agent

    def get(self, agent_id: str) -> AgentInfo | None:
        return self._store.get(agent_id)
    
    def delete(self, agent_id: str) -> bool:
        with self._lock:
            return self._store.pop(agent_id, None) is not None

    def list_all(self) -> list[AgentInfo]:
        return list(self._store.values())

    def query(self, capability: str = None, status: str = None) -> list[AgentInfo]:
        results = self.list_all()
        if capability:
            results = [
                a for a in results
                if any(c.name == capability for c in a.capabilities)
            ]
        if status:
            results = [a for a in results if a.status == status]
        return results

    def update_status(self, agent_id: str, status: str):
        with self._lock:
            if agent_id in self._store:
                self._store[agent_id].status = status
                self._store[agent_id].last_seen = datetime.utcnow()