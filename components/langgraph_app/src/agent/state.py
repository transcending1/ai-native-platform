from dataclasses import dataclass
from typing import TypedDict, Annotated, List

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


@dataclass
class InputState(TypedDict):
    question: str


@dataclass
class OutputState(TypedDict):
    answer: str


@dataclass
class State(InputState, OutputState):
    messages: Annotated[list[AnyMessage], add_messages]
    context: List[Document]
    tool_context: List[Document]
