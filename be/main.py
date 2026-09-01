import uvicorn , logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.route.agent_route import router as agent_router
from src.service.graph_agent_service import GraphAgentService

logger = logging.basicConfig(
    format="%(asctime)s %(clientip)-15s %(user)-8s %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    graph_agent_service = GraphAgentService()
    await graph_agent_service.start()
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
