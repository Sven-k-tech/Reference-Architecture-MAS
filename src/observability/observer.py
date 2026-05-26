"""The LangFuse CallbackHandler for tracing your Multi-Agent System"""
from langfuse.langchain import CallbackHandler


def get_handler() -> CallbackHandler:
    # Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST from env
    return CallbackHandler()


# Backwards-compatible alias
def observe() -> list:
    return [get_handler()]
