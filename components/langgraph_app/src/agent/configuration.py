from __future__ import annotations

import os
from dataclasses import dataclass, fields, field
from typing import Optional, TypeVar

from langchain_core.runnables import RunnableConfig

T = TypeVar("T")


@dataclass(kw_only=True)
class SysConfig:
    tenant_id: str = "none"
    user_id: str = "user1"
    owner: str = "user1"


@dataclass(kw_only=True)
class ChatBotConfig:
    prompt: str = "你是情感伴侣"


@dataclass(kw_only=True)
class RagConfig:
    prompt: str = "你是情感伴侣"
    is_rag: bool = True
    retrieve_top_n: int = 5
    retrieve_threshold: float = 0.2
    is_rerank: bool = True
    rerank_top_n: int = 3
    rerank_threshold: float = 0.4
    is_llm_rerank: bool = True
    namespace_list: list[str] = field(default_factory=lambda: ["namespace1"])
    is_structured_output: bool = True


@dataclass(kw_only=True)
class ToolConfig:
    is_rag: bool = True
    retrieve_top_n: int = 5
    retrieve_threshold: float = 0.2
    is_rerank: bool = True
    rerank_top_n: int = 3
    rerank_threshold: float = 0.4
    is_llm_rerank: bool = True
    max_iterations: int = 3
    namespace_list: list[str] = field(default_factory=lambda: ["namespace1"])


@dataclass(kw_only=True)
class MemoryConfig:
    max_tokens: int = 256


@dataclass(kw_only=True)
class Configuration:
    sys_config: SysConfig = field(default_factory=SysConfig)
    chat_bot_config: ChatBotConfig = field(default_factory=ChatBotConfig)
    rag_config: RagConfig = field(default_factory=RagConfig)
    tool_config: ToolConfig = field(default_factory=ToolConfig)
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)
    last_temperature: int = 0
    last_max_tokens: int = 512
    last_api_key: str = os.getenv('CHAT_MODEL_DEFAULT_API_KEY')
    last_extra_body: dict = None
    knowledge_rerank_temperature: int = 0
    knowledge_rerank_max_tokens: int = 512
    knowledge_rerank_api_key: str = os.getenv('CHAT_MODEL_DEFAULT_API_KEY')
    knowledge_rerank_extra_body: dict = None
    thread_id: str = None

    @classmethod
    def from_runnable_config(
            cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        configurable = (config.get("configurable") or {}) if config else {}
        _fields = {f.name for f in fields(cls) if f.init}

        for k, v in configurable.items():
            if k == 'sys_config':
                pass
            if k not in _fields:
                continue
            if isinstance(v, dict):
                if k == 'sys_config':
                    v = SysConfig(**v)
                elif k == 'chat_bot_config':
                    v = ChatBotConfig(**v)
                elif k == 'rag_config':
                    v = RagConfig(**v)
                elif k == 'memory_config':
                    v = MemoryConfig(**v)
                elif k == 'tool_config':
                    v = ToolConfig(**v)
                # set k v
                configurable[k] = v
        return cls(**{k: v for k, v in configurable.items() if k in _fields})
