from uuid import UUID
from pydantic import BaseModel 
from typing import Literal



class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    session_id: str
    messages: list[ChatMessage]

class AgentChatResponse(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str
    agent: str
    screenshot: str | None = None

class UsageInfo(BaseModel):
    total_tokens: int
    max_context_tokens: int
    threshold_percent: float
    percent_used: float
    should_summarize: bool

class SummarizeResponse(BaseModel):
    summary: str
    usage: UsageInfo