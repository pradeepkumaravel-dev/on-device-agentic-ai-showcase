import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from src.utilities.exception_utils import NormalExceptions
from src.schema.agent_schema import AgentChatResponse, ChatRequest, SummarizeResponse
from src.service.graph_agent_service import GraphAgentService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat"
)

@router.post("/chat-history")
async def get_chat_history(session_id, req:Request):
    try:
        logger.info("Desktop agent graph invoked")
        service: GraphAgentService = req.app.state.graph_agent_service
        response = await service.get_chat_history(session_id)
        return response        
        
    except Exception as e:
        raise NormalExceptions(message="error occurred at agent_route.py:/chat-history", error=str(e), log=False)
    except NormalExceptions:
        raise

@router.post("/desktop-agent", response_model=AgentChatResponse)
async def desktop_agent(request: ChatRequest, req: Request):
    try:
        logger.info("Desktop agent graph invoked")
        service: GraphAgentService = req.app.state.graph_agent_service
        response = await service.invoke(request.messages, request.session_id)
        return response

    except Exception as e:
        raise NormalExceptions(message="error occurred at agent_route.py:/desktop-agent", error=str(e), log=False)
    except NormalExceptions:
        raise


@router.post("/desktop-agent/stream")
async def desktop_agent_stream(request: ChatRequest, req: Request):
    try:
        service: GraphAgentService = req.app.state.graph_agent_service
        return StreamingResponse(
            service.stream(request.messages, request.session_id),
            media_type="text/event-stream",
        )
    except Exception as e:
        raise NormalExceptions(message="error occurred at agent_route.py:/desktop-agent/stream", error=str(e), log=False)
    except NormalExceptions:
        raise


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: ChatRequest, req: Request):
    try:
        logger.info("Summarize invoked")
        service: GraphAgentService = req.app.state.graph_agent_service
        response = await service.summarize(request.messages, request.session_id)
        return response

    except Exception as e:
        raise NormalExceptions(message="error occurred at agent_route.py:/summarize", error=str(e), log=False)
    except NormalExceptions:
        raise