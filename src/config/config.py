"""
Shared configuration settings for the multi-agent system
- API Keys (loaded from .env)
- LLM factory function
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_core.language_models.chat_models import BaseChatModel

#load .env file
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


#the base settings for the MAS
class Settings(BaseSettings):
    groq_api_key:        str = ""
    openai_api_key:      str = ""
    ollama_base_url:     str = "http://localhost:11434"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host:       str = "https://cloud.langfuse.com"
    zotero_api_key:      str = ""
    zotero_library_id:   str = ""
    taviley_api_key:     str = ""
    taviley_max_results: int = 5
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_llm(provider: str, model: str, temperature: float) -> BaseChatModel:
    settings = get_settings()
    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=temperature, api_key=settings.groq_api_key)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature, base_url=settings.ollama_base_url)
    else:
        raise ValueError(f"Unsupported provider '{provider}'. Use: groq, openai, anthropic, google, ollama")


