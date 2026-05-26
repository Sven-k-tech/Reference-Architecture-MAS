from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, ToolMessage
from src.agents.experts.base import BaseAgent
from src.agents.prompts.prompts import WORKER_PROMPT
from src.agents.tools.tools import worker_tool


class ResearcherAgent(BaseAgent):

    # ------------------------------------------------------------------
    # Define the metadata for your worker agent
    # ------------------------------------------------------------------

    name            = ""
    domain          = ""
    capabilities    = [""]
    llm_provider    = ""
    llm_name        = ""
    llm_temperature = 0.2

    def build_agent(self):

        # ------------------------------------------------------------------
        # Build your agent using the create_agent method. Define the model,
        # tools, System Prompt, etc.
        # ------------------------------------------------------------------
        return


    def invoke(self) -> str:
        # ------------------------------------------------------------------
        # Invoke your Agent and pass a message 
        # ------------------------------------------------------------------
        return