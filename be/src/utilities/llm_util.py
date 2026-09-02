import logging 
from langchain_ollama import ChatOllama
from src.utilities.exception_utils import NormalExceptions
from src.config import MAX_CONTEXT_TOKENS

logger = logging.getLogger(__name__)

class LLMUtil:
    def __init__(self,model_type):
        self.model_type = model_type 

    def get_model(self, reasoning=True):
        try:
            if self.model_type == "local":
                logger.info("current model is qwen")
                llm = self._get_qwen(reasoning)
            else:
                logger.info("Other models are yet to be configured")
            return llm
        except NormalExceptions :
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in llm_util.py", error=str(e), log=True)


    def _get_qwen(self, reasoning=True):
        try:
            llm = ChatOllama(model="qwen3:1.7b", reasoning=reasoning, num_ctx=MAX_CONTEXT_TOKENS)
            return llm
        except NormalExceptions :
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in llm_util.py", error=str(e), log=True)