from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, ToolMessage
from src.agents.experts.base import BaseAgent
from src.agents.prompts.prompts import RESEARCHER_PROMPT
from src.agents.tools.tools import arxiv_search


class ResearcherAgent(BaseAgent):
    # ------------------------------------------------------------------
    # Define the Metadata of your agent
    # ------------------------------------------------------------------
    name            = "RandyResearch"
    domain          = "research"
    capabilities    = ["arxiv_retrieve"]
    llm_provider    = "groq"
    llm_name        = "llama-3.3-70b-versatile"
    llm_temperature = 0.2

    def build_agent(self):
        # ------------------------------------------------------------------
        # Build your agent using the create_agent method. Define the model,
        # tools, System Prompt, etc.
        # ------------------------------------------------------------------
        return create_agent(
            model=self.llm,
            tools=[arxiv_search],
            system_prompt=RESEARCHER_PROMPT,
        )

    def invoke(self, task: str, callbacks: list = None) -> str:
        # ------------------------------------------------------------------
        # Invoke your Agent and pass a message 
        # ------------------------------------------------------------------
        result = self.agent.invoke(
            {"messages": [HumanMessage(content=task)]},
            config={"callbacks": callbacks or [], "recursion_limit": 10},
        )

        #returns the last tool message
        for msg in reversed(result["messages"]):
            if isinstance(msg, ToolMessage):
                return msg.content
        return str(result["messages"][-1].content)
