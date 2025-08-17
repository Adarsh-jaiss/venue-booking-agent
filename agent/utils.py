import typing
import logging
import uuid

from langgraph.types import Interrupt
from langchain_core.messages import AIMessageChunk, AIMessage, ToolMessage
from agent.models import CategoryEnum, ChunkPayload, ResponseEnum



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class StreamHandler:
    """Stream handler for the agent"""

    def __init__(self):
        self.tool_message: bool = False
        self.tool_name: str | None = None
        self.tool_id: str | None = None


    def process_chunk(self, chunk: tuple[str, typing.Any]):
        """Process a chunk of a streaming response with the stream mode set to messages"""
        category, value = chunk
        # logger.error(f"Recieved chunk: {category}\n{value}")

        if category == "updates":
            if value.get("__interrupt__"):
                interrupt, = value.get("__interrupt__")
                # logger.error(f"Recieved interrupt: {interrupt} of type {type(interrupt)}")

                if isinstance(interrupt, Interrupt):
                    payload = ChunkPayload(id=str(uuid.uuid4()), type=ResponseEnum.Response, category=CategoryEnum.Interrupt, content=interrupt.value)
                    yield payload.model_dump_json()

            if(value.get("agent")):
                [message] = value.get("agent", {}).get("messages")
                logger.error(f"Recieved update from agent: {message}")

                if isinstance(message, AIMessage):
                    metadata = message.response_metadata
                    finish_reason = metadata.get("finish_reason")

                    if finish_reason == "tool_calls":
                        [tool] = message.tool_calls or []

                        if tool and tool.get("name") != "user-assistance":
                            self.tool_message = True
                            self.tool_name = tool.get("name")
                            self.tool_id = tool.get("id")
                            
                            content = {"name": self.tool_name, "content": tool.get("args")}
                            payload = ChunkPayload(id=self.tool_id, type=ResponseEnum.Start, category=CategoryEnum.Reasoning, content=content)
                            yield payload.model_dump_json()
            
            if(value.get("tools")): 
                messages = value.get("tools", {}).get("messages")
                logger.error(f"Recieved tool message: {messages}")
                self.tool_message = False

                for message in messages:
                    if isinstance(message, ToolMessage) and message.name != "user-assistance":
                        content = {"name": message.name, "content": message.content, "artifact": message.artifact}
                        payload = ChunkPayload(id=self.tool_id, type=ResponseEnum.End, category=CategoryEnum.Reasoning, content=content)
                        yield payload.model_dump_json()


        if category == "messages":
            if isinstance(value, tuple):
                token, metadata = value
                # logger.error(f"Recieved LLM Token: {token}")

                if isinstance(token, AIMessageChunk):
                    if self.tool_message and self.tool_id and self.tool_name and self.tool_name != "user-assistance":
                        # logger.error(f"Received AIMessageChunk from tool {token}")
                        content = {"name": self.tool_name, "content": token.content}
                        payload = ChunkPayload(id=self.tool_id, type=ResponseEnum.End, category=CategoryEnum.ReasoningChunk, content=content)
                        yield payload.model_dump_json()
                    else:
                        # logger.error(f"Received AIMessageChunk from agent {token}")
                        payload = ChunkPayload(id=token.id, type=ResponseEnum.Response, category=CategoryEnum.TextChunk, content=token.content)
                        yield payload.model_dump_json()
