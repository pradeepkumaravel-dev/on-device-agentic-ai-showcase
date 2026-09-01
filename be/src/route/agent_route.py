import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from src.utilities.exception_utils import NormalExceptions
from src.schema.agent_schema import AgentChatResponse, ChatRequest, SummarizeResponse
from src.service.graph_agent_service import GraphAgentService
import aiosqlite
from src.config import DB_FILE_PATH

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat"
)

@router.get("/sessions")
async def get_sessions():
    try:
        async with aiosqlite.connect(DB_FILE_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        raise NormalExceptions(message="error occurred at agent_route.py:/sessions", error=str(e), log=False)
    except NormalExceptions:
        raise

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    try:
        async with aiosqlite.connect(DB_FILE_PATH) as conn:
            await conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await conn.commit()
            return {"status": "success"}
    except Exception as e:
        raise NormalExceptions(message="error occurred at agent_route.py:/sessions (DELETE)", error=str(e), log=False)
    except NormalExceptions:
        raise

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