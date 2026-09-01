import logging
from typing import Literal

from pydantic import BaseModel
from src.service.graph.state import GraphState
from src.utilities.exception_utils import NormalExceptions
from src.utilities.llm_util import LLMUtil
from src.utilities.message_utils import last_human_text

logger = logging.getLogger(__name__)

SUPERVISOR_SYSTEM_PROMPT = """You are a router. Classify the user's message into exactly one route:
- "desktop": launching/opening apps, files, or URLs; system stats (CPU, RAM, GPU); getting or setting system volume.
- "screen": asking what is currently on screen, to look at / describe / read the screen.
- "chat": anything else (general questions, conversation, knowledge questions).

Examples:
"open notepad" -> desktop
"launch chrome" -> desktop
"what is my cpu usage" -> desktop
"set volume to 50" -> desktop
"how much ram am i using" -> desktop
"what is on my screen right now" -> screen
"describe what im looking at" -> screen
"take a screenshot and tell me what you see" -> screen
"what is the capital of france" -> chat
"tell me a joke" -> chat
"how are you" -> chat
"""


class RouteDecision(BaseModel):
    route: Literal["chat", "desktop", "screen"]


class SupervisorNode:
    def __init__(self):
        self.llm = LLMUtil(model_type="local").get_model()
        self.structured_llm = self.llm.with_structured_output(RouteDecision)

    async def route(self, state: GraphState) -> dict:
        try:
            user_text = last_human_text(state["messages"])
            decision: RouteDecision = await self.structured_llm.ainvoke(
                [("system", SUPERVISOR_SYSTEM_PROMPT), ("user", user_text)]
            )
            logger.info("supervisor routed to %s", decision.route)
            return {"route": decision.route}
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in supervisor.py", error=str(e), log=True)
