from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    session_id: str
    route: Optional[Literal["chat", "desktop", "screen"]]
    agent_used: Optional[str]
    screenshot_b64: Optional[str]
    turn_usage: Optional[dict]
