import json
import logging
import os
import asyncio
import aiosqlite
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from src import config
from src.schema.agent_schema import ChatMessage
from src.service.graph.build_graph import GraphBuilder
from src.config import ROLE_MAP
from src.utilities.exception_utils import NormalExceptions
from src.utilities.llm_util import LLMUtil

logger = logging.getLogger(__name__)

DESKTOP_TOOLS_SCRIPT = Path(__file__).resolve().parent.parent / "mcp_server" / "desktop_tools.py"

GRAPH_NODES = {"supervisor", "chat", "desktop", "screen"}
# Nodes whose text is streamed to the frontend as thinking/token events.
# Both chat and desktop are create_react_agent subgraphs internally, and
# create_react_agent always names its own LLM-calling node "agent" - so a
# static {internal_name: outer_name} map can't tell a chat turn's stream
# chunks apart from a desktop turn's (both report node="agent"). Instead,
# `stream()` tracks whichever of these outer nodes most recently started and
# attributes any nested chat-model chunk to that - unambiguous since the
# supervisor only ever routes to one of them per turn.
TEXT_STREAMING_OUTER_NODES = {"chat", "desktop"}

SUMMARIZE_PROMPT = (
    "Summarize the conversation above concisely, preserving the facts and "
    "context needed to continue it. Write the summary as plain prose, not a transcript."
)


def _usage_payload(turn_usage: dict | None) -> dict:
    total = turn_usage.get("total_tokens", 0) if turn_usage else 0
    percent_used = round(total / config.MAX_CONTEXT_TOKENS * 100, 1)
    return {
        "total_tokens": total,
        "max_context_tokens": config.MAX_CONTEXT_TOKENS,
        "threshold_percent": config.SUMMARY_THRESHOLD_PERCENT,
        "percent_used": percent_used,
        "should_summarize": percent_used >= config.SUMMARY_THRESHOLD_PERCENT,
    }


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


class GraphAgentService:
    def __init__(self):
        # Full env is passed (rather than MCP's default restricted allowlist)
        # since this is our own trusted local server, not a third-party one -
        # tools like nvidia-smi (via get_system_info) need vars such as
        # ProgramFiles/ProgramData/windir that the default allowlist omits.
        self.mcp_client = MultiServerMCPClient(
            {
                "desktop": {
                    "command": "uv",
                    "args": ["run", "python", str(DESKTOP_TOOLS_SCRIPT)],
                    "transport": "stdio",
                    "env": dict(os.environ),
                }
            }
        )
        self.graph = None

    async def start(self, checkpointer=None):
        try:
            tools = await self.mcp_client.get_tools()
            self.graph = GraphBuilder(tools).build(checkpointer)
            logger.info("desktop agent graph ready with tools: %s", [t.name for t in tools])
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in graph_agent_service.py:start", error=str(e), log=True)

    def _initial_state(self, messages: list[ChatMessage], session_id: str) -> dict:
        lc_messages = [ROLE_MAP[m.role](content=m.content) for m in messages]
        return {
            "messages": lc_messages,
            "session_id": session_id,
            "route": None,
            "agent_used": None,
            "screenshot_b64": None,
            "turn_usage": None,
        }

    async def invoke(self, messages: list[ChatMessage], session_id: str) -> dict:
        try:
            result = await self.graph.ainvoke(self._initial_state(messages, session_id))
            return {
                "role": "assistant",
                "content": result["messages"][-1].content,
                "agent": result["agent_used"],
                "screenshot": result.get("screenshot_b64"),
            }
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in graph_agent_service.py", error=str(e), log=True)

    async def _generate_session_title(self, first_message: str) -> str:
        try:
            llm = LLMUtil(model_type="local").get_model()
            prompt = f"Generate a short title (max 5 words) for this chat based on the first message. Only return the title, no quotes or explanation. Message: {first_message}"
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip().strip('\"').strip("'\'")
        except Exception as e:
            logger.error(f"Error generating session title: {e}")
            return "New Chat"

    async def stream(self, messages: list[ChatMessage], session_id: str):
        try:
            is_new_session = False
            title_task = None
            async with aiosqlite.connect(config.DB_FILE_PATH) as conn:
                cursor = await conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
                row = await cursor.fetchone()
                if not row:
                    is_new_session = True
                    await conn.execute(
                        "INSERT INTO sessions (id, title) VALUES (?, ?)", 
                        (session_id, "New Chat")
                    )
                else:
                    await conn.execute(
                        "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                        (session_id,)
                    )
                await conn.commit()

            if is_new_session and messages:
                first_msg = messages[0].content
                title_task = asyncio.create_task(self._generate_session_title(first_msg))

            graph_config = {
                "configurable": {
                    "thread_id": session_id 
                }
            }
            root_run_id = None
            active_outer_node = None
            async for event in self.graph.astream_events(
                self._initial_state(messages, session_id), version="v2" , config=graph_config
            ):
                if root_run_id is None:
                    # The very first event is always the outer graph's own
                    # on_chain_start - its run_id anchors "the whole run is
                    # done" below. Needed because create_react_agent's inner
                    # subgraph is *also* named "LangGraph" and emits its own
                    # on_chain_end, which would otherwise fire "done" early.
                    root_run_id = event.get("run_id")

                et = event["event"]
                name = event.get("name")
                node = event.get("metadata", {}).get("langgraph_node")

                if node in GRAPH_NODES and name == node:
                    if et == "on_chain_start":
                        if node in TEXT_STREAMING_OUTER_NODES:
                            active_outer_node = node
                        yield _sse({"type": "node_start", "node": node})
                    elif et == "on_chain_end":
                        yield _sse({"type": "node_end", "node": node})

                elif et == "on_chat_model_stream" and active_outer_node is not None:
                    chunk = event["data"]["chunk"]
                    reasoning_content = chunk.additional_kwargs.get("reasoning_content")
                    if reasoning_content:
                        yield _sse({"type": "thinking", "node": active_outer_node, "content": reasoning_content})
                    elif chunk.content:
                        yield _sse({"type": "token", "node": active_outer_node, "content": chunk.content})

                elif et == "on_chain_end" and name == "LangGraph" and event.get("run_id") == root_run_id:
                    final_state = event["data"]["output"]
                    yield _sse(
                        {
                            "type": "done",
                            "content": final_state["messages"][-1].content,
                            "agent": final_state.get("agent_used"),
                            "screenshot": final_state.get("screenshot_b64"),
                            "usage": _usage_payload(final_state.get("turn_usage")),
                        }
                    )
                    
            if title_task:
                title = await title_task
                async with aiosqlite.connect(config.DB_FILE_PATH) as conn:
                    await conn.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
                    await conn.commit()
                yield _sse({"type": "session_title", "title": title})
                
        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})

    async def summarize(self, messages: list[ChatMessage], session_id: str) -> dict:
        try:
            lc_messages = [ROLE_MAP[m.role](content=m.content) for m in messages]
            llm = LLMUtil(model_type="local").get_model()
            # The instruction goes AFTER the history as a trailing HumanMessage,
            # not before it as a SystemMessage: qwen3's chat template emits an
            # immediate stop token when asked to generate right after a
            # conversation that already ends on an AIMessage (verified: 4/4
            # reproducible empty responses with a leading-SystemMessage prompt
            # whose history ends on an AI turn; 0/3 failures once the prompt
            # itself became the final, trailing Human turn).
            response = await llm.ainvoke([*lc_messages, HumanMessage(content=SUMMARIZE_PROMPT)])
            return {"summary": response.content, "usage": _usage_payload(response.usage_metadata)}
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in graph_agent_service.py:summarize", error=str(e), log=True)

    async def get_chat_history(self,session_id:str):
        try:
            config = {"configurable": {"thread_id": session_id}}
            state_snapshot = await self.graph.aget_state(config)
            messages = state_snapshot.values.get("messages", [])
            print(messages)
            return messages 
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in graph_agent_service.py:summarize", error=str(e), log=True)
