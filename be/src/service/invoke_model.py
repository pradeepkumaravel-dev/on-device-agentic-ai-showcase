import logging 
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_ollama import ChatOllama
from src.utilities.exception_utils import NormalExceptions
from src.utilities.llm_util import LLMUtil


logger = logging.getLogger(__name__)


ROLE_MAP = {
    "system": SystemMessage,
    "user": HumanMessage,
    "assistant": AIMessage,
}

class InvokeModelService():
    def __init__(self,repository,model_type):
        self.repo = repository
        self.llm:ChatOllama = LLMUtil(model_type=model_type).get_model()

    async def invoke_model(self,messages):
        try:
            lc_messages = [ROLE_MAP[m.role](content=m.content) for m in messages]
            response = await self.llm.ainvoke(lc_messages)
            return {"role": "assistant", "content": response.content}
        except NormalExceptions:
            raise 
        except Exception as e:
            raise NormalExceptions(message="exception occurred at invoke_model.py" , error=str(e) , log=True)