from typing import TypedDict
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, StateGraph
from src.config.config import get_llm




# ------------------------------------------------------------------
# Define the State of your Supervisor Graph
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Configure your Supervisor with get_llm
# ------------------------------------------------------------------
supervisor_llm = get_llm("", "", 0.0)


# ------------------------------------------------------------------
# Define the Nodes of your Supervisor graph
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Build your Supervisor Graph
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Add your Supervisor Graph Nodes
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Connect your Supervisor Graph Nodes
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Compile your Supervisor Graph
# ------------------------------------------------------------------

