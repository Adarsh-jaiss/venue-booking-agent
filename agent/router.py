import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from agent.models import ChatInput, ChoicesInput
from agent.main import stream, resume, invoke




router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/discovery")
def discovery():
    """Return the discovery of the agent"""
    return JSONResponse({"name": "Creative Director Agent","slug": "creative-director-agent",})


@router.post("/invoke")
async def invoke_route(body: ChatInput):
    """Return the complete data after it is generated without steps and reasoning, to be used by other agents"""
    response = await invoke(body.prompt, body.session, body.user_id, body.organization_id)
    return JSONResponse(response)


@router.post("/stream")
async def stream_route(body: ChatInput):
    """Will stream the values when calling the agent directly with reasoning and everything"""

    logger.info(f"Invoking streaming response for {body}")
    response =  stream(body.prompt, body.session, body.user_id, body.organization_id) if isinstance(body.prompt, str)  else resume(body.prompt, body.session, body.user_id, body.organization_id)
    return StreamingResponse(response, media_type="text/event-stream")
