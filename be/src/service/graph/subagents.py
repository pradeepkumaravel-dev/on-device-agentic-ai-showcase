import logging

import ollama
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from src.service.graph.research_tools import fetch_page, web_search
from src.service.graph.state import GraphState
from src.utilities.exception_utils import NormalExceptions
from src.utilities.llm_util import LLMUtil
from src.utilities.message_utils import last_human_text

VISION_MODEL = "moondream"
TEXT_MODEL = "qwen3:1.7b"

logger = logging.getLogger(__name__)

CHAT_AGENT_PROMPT = (
    "You are a helpful research assistant with two tools: web_search and fetch_page.\n\n"
    "You MUST call web_search first (before answering) whenever the question involves:\n"
    "- current events, news, or anything time-sensitive (\"latest\", \"current\", \"today\", \"this year\", \"now\")\n"
    "- version numbers, releases, or specifications of software/products\n"
    "- facts you are not 100% certain of\n"
    "- an explicit request to research or report on something\n\n"
    "Only skip searching for pure opinion questions, casual conversation, or math/logic you can solve directly.\n\n"
    "After web_search, if the snippets do not clearly state the answer, call fetch_page on the most "
    "relevant URL to read the full page before answering - do not guess. If you still cannot find a "
    "clear answer after searching and fetching, say so explicitly rather than making one up.\n\n"
    "When you have done research, write a comprehensive, well-organized report: use headings or bullet "
    "points, synthesize across sources rather than listing them separately, and cite each source URL."
)

DESKTOP_AGENT_PROMPT = (
    "You control the user's Windows PC via tools: taking screenshots, reading "
    "system info (CPU/RAM/GPU), launching apps/files/URLs, and reading/setting "
    "system volume. Only take safe, reversible actions. After using a tool, "
    "report the result back to the user concisely in plain language."
)


class SubAgentNodes:
    def __init__(self, tools):
        try:
            self.chat_agent = create_react_agent(
                model=LLMUtil(model_type="local").get_model(),
                tools=[web_search, fetch_page],
                prompt=CHAT_AGENT_PROMPT,
            )
            self.desktop_agent = create_react_agent(
                model=LLMUtil(model_type="local").get_model(), tools=tools, prompt=DESKTOP_AGENT_PROMPT
            )
            self.screenshot_tool = next(t for t in tools if t.name == "take_screenshot")
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in subagents.py:__init__", error=str(e), log=True)

    async def chat_node(self, state: GraphState) -> dict:
        try:
            result = await self.chat_agent.ainvoke({"messages": state["messages"]})
            final_message = result["messages"][-1]
            return {
                "messages": [final_message],
                "agent_used": "chat",
                "turn_usage": getattr(final_message, "usage_metadata", None),
            }
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in subagents.py:chat_node", error=str(e), log=True)

    async def desktop_node(self, state: GraphState) -> dict:
        try:
            result = await self.desktop_agent.ainvoke({"messages": state["messages"]})
            final_message = result["messages"][-1]
            return {
                "messages": [final_message],
                "agent_used": "desktop",
                "turn_usage": getattr(final_message, "usage_metadata", None),
            }
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in subagents.py:desktop_node", error=str(e), log=True)

    async def screen_node(self, state: GraphState) -> dict:
        try:
            raw_result = await self.screenshot_tool.ainvoke({})
            # MCP tool results come back as a list of content blocks, e.g.
            # [{"type": "text", "text": "<base64 png>", "id": "..."}]
            b64_png = raw_result[0]["text"] if isinstance(raw_result, list) else raw_result
            user_text = last_human_text(state["messages"])
            # Calls the ollama client directly rather than going through ChatOllama:
            # ChatOllama's message converter always prepends a leading "\n" to text
            # content, and moondream's chat template is sensitive enough to that
            # that it emits an immediate stop token (empty response) when it's there.
            client = ollama.AsyncClient()
            # On a 4GB-VRAM GPU, qwen3 (supervisor/desktop agent) and moondream can
            # both stay resident at once but leave little headroom, which makes
            # moondream's occasional empty-output flakiness worse. Force qwen3 out
            # of VRAM first so moondream gets the full budget.
            await client.generate(model=TEXT_MODEL, prompt="", keep_alive=0)
            description = ""
            turn_usage = None
            # moondream still occasionally emits an immediate stop token (empty
            # response) even with full VRAM headroom - retry a few times before
            # giving up, each retry is cheap relative to the risk of a blank reply.
            for _ in range(3):
                response = await client.chat(
                    model=VISION_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Describe what's on this screen. User asked: {user_text}",
                            "images": [b64_png],
                        }
                    ],
                    stream=False,
                )
                prompt_tokens = response.get("prompt_eval_count", 0)
                completion_tokens = response.get("eval_count", 0)
                turn_usage = {
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                }
                description = response["message"]["content"].strip()
                if description:
                    break
            return {
                "messages": [AIMessage(content=description)],
                "agent_used": "screen",
                "screenshot_b64": b64_png,
                "turn_usage": turn_usage,
            }
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in subagents.py:screen_node", error=str(e), log=True)
