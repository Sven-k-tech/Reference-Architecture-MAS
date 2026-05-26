"""implements a blackboard the Expert Agents can use for collaborating"""
import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

_DEFAULT_PERSISTENCE_PATH = Path(__file__).parent / "blackboard_state.json"


class KnowledgeDomain(str, Enum):
    RESEARCH     = "research"
    LIBRARY      = "library"

class KnowledgeEntry(BaseModel):
    domain:     str
    key:        str
    value:      Any
    agent_id:   str
    metadata:   dict[str, Any] = {}
    written_at: datetime = None
    version:    int = 1

    def model_post_init(self, __context):
        """Set written_at to the current UTC time if not provided."""
        if not self.written_at:
            self.written_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert knowledge entry to dictionary."""
        return {
            "domain":     self.domain,
            "key":        self.key,
            "value":      self.value,
            "agent_id":   self.agent_id,
            "metadata":   self.metadata,
            "written_at": self.written_at.isoformat(),
            "version":    self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeEntry":
        """Create knowledge entry from dictionary."""
        entry = cls(
            domain=data["domain"],
            key=data["key"],
            value=data["value"],
            agent_id=data["agent_id"],
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
        )
        entry.written_at = datetime.fromisoformat(data["written_at"])
        return entry

class Blackboard:
    _instance: "Blackboard | None" = None
    _init_lock = threading.Lock()
    _knowledge: dict
    _notifications: dict
    _rw_lock: asyncio.Lock
    _persistence_path: Path

    def __new__(cls, persistence_path: Path | None = None):
        """
        Return the single shared Blackboard instance (singleton).
        The first call creates the instance; all subsequent calls return the same object.

        Args:
            persistence_path: Optional path for the JSON persistence file.
                              Defaults to blackboard_state.json next to this module.
        """
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._knowledge = {d.value: {} for d in KnowledgeDomain}
                    inst._notifications = {}
                    inst._rw_lock = asyncio.Lock()
                    inst._persistence_path = persistence_path or _DEFAULT_PERSISTENCE_PATH
                    cls._instance = inst
        return cls._instance

    # Core API
    async def write_knowledge(
        self,
        domain: str,
        key: str,
        value: Any,
        agent_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeEntry:
        """
        Write knowledge to the blackboard.

        If an entry already exists at (domain, key) its version is incremented.
        After writing, all other registered agents receive a notification and
        the state is persisted to disk.

        Args:
            domain:   Knowledge domain (e.g. 'requirements', 'architecture')
            key:      Entry key within the domain (e.g. 'req-001')
            value:    The knowledge value to store
            agent_id: ID of the agent writing the knowledge
            metadata: Optional dict with additional context about the entry

        Returns:
            The created or updated KnowledgeEntry
        """
        if domain not in self._knowledge:
            self._knowledge[domain] = {}

        async with self._rw_lock:
            existing = self._knowledge[domain].get(key)
            entry = KnowledgeEntry(
                domain=domain,
                key=key,
                value=value,
                agent_id=agent_id,
                metadata=metadata or {},
                version=(existing.version + 1) if existing else 1,
            )
            self._knowledge[domain][key] = entry

        logger.debug("blackboard write: %s.%s by %s (v%d)", domain, key, agent_id, entry.version)
        await self._notify_agents(domain, key, agent_id)
        await self._persist()
        return entry

    async def read_knowledge(
        self,
        domain: str,
        key: str | None = None,
        agent_id: str | None = None,
    ) -> Any:
        """
        Read knowledge from the blackboard.

        Args:
            domain:   Knowledge domain to read from
            key:      Specific entry key to read. If None, the entire domain is returned.
            agent_id: ID of the agent reading (used for logging only)

        Returns:
            A single value when key is given, or a {key: value} dict for the whole domain.
            Returns None if the requested key does not exist.
        """
        domain_data = self._knowledge.get(domain, {})
        if key is not None:
            entry = domain_data.get(key)
            if entry:
                logger.debug("blackboard read: %s.%s by %s", domain, key, agent_id)
                return entry.value
            return None
        return {k: v.value for k, v in domain_data.items()}

    async def read_all(self) -> dict[str, dict[str, Any]]:
        """
        Read every entry across all domains.

        Returns:
            Nested dict: {domain: {key: value}} for all non-empty domains.
        """
        return {
            domain: {k: v.value for k, v in entries.items()}
            for domain, entries in self._knowledge.items()
        }

    async def clear(self, domain: str | None = None) -> None:
        """
        Clear entries from the blackboard.

        Args:
            domain: Domain to clear. If None, all domains are cleared.
        """
        async with self._rw_lock:
            if domain:
                if domain in self._knowledge:
                    self._knowledge[domain] = {}
            else:
                for d in list(self._knowledge):
                    self._knowledge[d] = {}
        await self._persist()



    # Convenience aliases so tools.py and agents can use shorter names
    write = write_knowledge
    read  = read_knowledge



    # Notification system
    def register_agent(self, agent_id: str) -> None:
        """
        Register an agent to receive change notifications.

        Must be called before an agent starts working so it does not miss
        writes by other agents. Each agent only receives notifications for
        domains/keys written by other agents, not its own writes.

        Args:
            agent_id: Unique ID of the agent to register
        """
        if agent_id not in self._notifications:
            self._notifications[agent_id] = []
            logger.info("Agent registered for notifications: %s", agent_id)

    async def get_notifications(self, agent_id: str) -> list[dict]:
        """
        Get and clear all pending notifications for an agent.

        Each call drains the notification queue — the same events will not be
        returned again on the next call.

        Args:
            agent_id: ID of the agent requesting notifications

        Returns:
            List of notification dicts, each with domain, key, source_agent, timestamp.
        """
        notifications = self._notifications.get(agent_id, [])
        self._notifications[agent_id] = []
        return notifications

    async def _notify_agents(self, domain: str, key: str, source_agent: str) -> None:
        """
        Push a write event to every registered agent except the one that wrote it.

        Args:
            domain:       Domain that was written to
            key:          Key that was written
            source_agent: Agent that performed the write (excluded from notification)
        """
        event = {
            "domain":       domain,
            "key":          key,
            "source_agent": source_agent,
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        }
        for agent_id, queue in self._notifications.items():
            if agent_id != source_agent:
                queue.append(event)


    # Persistence
    async def load(self) -> None:
        """
        Load persisted blackboard state from disk.

        Call this once at application startup to restore state from a previous run.
        If no persistence file exists, the blackboard starts empty.
        """
        if not self._persistence_path.exists():
            return
        try:
            with open(self._persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for domain, entries in data.get("knowledge", {}).items():
                self._knowledge.setdefault(domain, {})
                for k, raw in entries.items():
                    self._knowledge[domain][k] = KnowledgeEntry.from_dict(raw)
            logger.info("blackboard loaded from %s", self._persistence_path)
        except Exception as e:
            logger.error("blackboard load failed: %s", e)

    async def _persist(self) -> None:
        """
        Save the current blackboard state to disk as JSON.

        Uses an atomic write (temp file + rename) to avoid corrupting the
        persistence file if the process is interrupted mid-write.
        Called automatically after every write and clear.
        """
        try:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "knowledge": {
                    domain: {k: v.to_dict() for k, v in entries.items()}
                    for domain, entries in self._knowledge.items()
                },
            }
            tmp = self._persistence_path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            tmp.replace(self._persistence_path)
        except Exception as e:
            logger.error("blackboard persist failed: %s", e)



    # Stats
    def stats(self) -> dict[str, Any]:
        """
        Return a summary of the current blackboard state.

        Returns:
            Dict with total_entries count and a per-domain breakdown
            of entry count and key names.
        """
        return {
            "total_entries": sum(len(e) for e in self._knowledge.values()),
            "domains": {
                d: {"count": len(e), "keys": list(e.keys())}
                for d, e in self._knowledge.items()
                if e
            },
        }
