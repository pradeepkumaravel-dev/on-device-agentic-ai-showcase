import uvicorn , logging , aiosqlite
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from src.config import DB_FILE_PATH
from src.route.agent_route import router as agent_router
from src.service.graph_agent_service import GraphAgentService
from dotenv import load_dotenv
load_dotenv


logger = logging.basicConfig(
    format="%(asctime)s %(clientip)-15s %(user)-8s %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with aiosqlite.connect(DB_FILE_PATH) as conn:
        checkpointer = AsyncSqliteSaver(conn)
        graph_agent_service = GraphAgentService()
        await graph_agent_service.start(checkpointer=checkpointer)
        app.state.graph_agent_service = graph_agent_service
        yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],

)

app.include_router(agent_router)


if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=False)
