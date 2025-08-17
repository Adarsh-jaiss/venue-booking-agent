from enum import Enum
from typing import Any
from pydantic import BaseModel


class CategoryEnum(str, Enum):
    Text = "text"
    Interrupt = "interrupt"
    Reasoning = "reasoning"
    TextChunk = "text.chunk"
    ReasoningChunk = "reasoning.chunk"


class ResponseEnum(str, Enum):
    End = "response.end"
    Start = "response.start"
    Response = "response"
    Error = "response.error"


class ChunkPayload(BaseModel):
    id: str
    content: Any
    type: ResponseEnum
    category: CategoryEnum


class ChatInput(BaseModel):
    session: str
    user_id: str
    prompt: str | dict
    organization_id: str


class ChoicesInput(BaseModel):    
    session: str
    