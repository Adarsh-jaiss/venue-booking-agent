from fastapi import FastAPI
from contextlib import asynccontextmanager
from agent.main import initialize
# from shared.database import connect_database, disconnect_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    agent = await initialize()
    app.state.agent = agent

    yield
