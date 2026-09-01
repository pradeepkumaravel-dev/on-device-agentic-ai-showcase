import logging

from src.utilities.exception_utils import NormalExceptions

logger = logging.getLogger(__name__)


def last_human_text(messages: list) -> str:
    try:
        for m in reversed(messages):
            if getattr(m, "type", None) == "human":
                return m.content
        return messages[-1].content if messages else ""
    except NormalExceptions:
        raise
    except Exception as e:
        raise NormalExceptions(message="exception occurred in message_utils.py", error=str(e), log=True)
