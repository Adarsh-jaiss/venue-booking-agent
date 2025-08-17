from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from lifespan import lifespan
from agent.router import router
from agent.main import agent_ctx

import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agent.log', mode='a')
    ],
    force=True
)

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.info("FastAPI backend starting...")

app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def agent_context_middleware(request: Request, call_next):
    logger.info(f"Processing request: {request.method} {request.url}")
    agent = request.app.state.agent
    token = agent_ctx.set(agent)
    try:
        response = await call_next(request)
        logger.info(f"Request completed: {request.method} {request.url} - Status: {response.status_code}")
    finally:
        agent_ctx.reset(token)
    return response


@app.get("/heartbeat")
async def heartbeat():
    logger.info("Heartbeat request received")
    return JSONResponse({"status": "ok", "version": "0.0.20"})


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server with uvicorn...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )