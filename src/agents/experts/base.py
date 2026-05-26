from abc import ABC, abstractmethod
from src.config.config import get_llm
from src.blackboard.blackboard import Blackboard
from src.registry.agent_registry.registry import register_agent as registry_register


class BaseAgent(ABC):
    """
    Abstract base class for all worker agents.

    __init__ orchestrates the startup sequence for every agent:
      1. Build llm_config from class attributes and register in the AgentRegistry
      2. Register in the Blackboard (to receive change notifications)
      3. configure_agent() — sets self.llm from the class-level LLM attributes
      4. build_agent()     — subclass assembles the LangGraph agent and returns it

    Subclasses declare their identity and LLM config as class attributes,
    then only implement build_agent() and invoke(). No __init__ override needed.
    """

    name:            str       = "BaseAgent"
    domain:          str       = ""
    capabilities:    list[str] = []
    llm_provider:    str       = ""
    llm_name:        str       = ""
    llm_temperature: float     = 0.0

    def __init__(self):
        llm_config = {
            "llm_provider":    self.llm_provider,
            "llm_name":        self.llm_name,
            "llm_temperature": self.llm_temperature,
        }
        self.agent_id = registry_register(self.name, self.capabilities, llm_config)
        Blackboard().register_agent(self.name)
        self.configure_agent()
        self.agent = self.build_agent()

    def configure_agent(self) -> None:
        """Instantiate self.llm from the class-level LLM attributes."""
        self.llm = get_llm(self.llm_provider, self.llm_name, self.llm_temperature)

    @abstractmethod
    def build_agent(self):
        """
        Build and return the LangGraph agent using self.llm and agent-specific tools/prompt.
        self.llm is guaranteed to be set when this is called.
        The return value is assigned to self.agent by __init__.
        """
        ...

    @abstractmethod
    def invoke(self, task: str, callbacks: list = None) -> str:
        """
        Run the agent on a task string and return the result as a plain string.
        Extract the final AIMessage content from the agent's response dict.
        """
        ...
