import logging
import contextvars

from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from agent.prompts import SYSTEM_PROMPT
from agent.utils import StreamHandler
from search.search import search_venues
from agent.memory import create_checkpointer
from langgraph.prebuilt import create_react_agent

from configs.settings import OPENAI_MODEL



logger = logging.getLogger(__name__)
agent_ctx = contextvars.ContextVar("agent")


async def initialize():
    """Initialize the agent in the context of the app. Returns the agent."""
    try:
        tools = [
            search_venues
        ]

        checkpointer = await create_checkpointer()
        llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.3, streaming=True)
        
        # Create the agent with proper error handling
        agent = create_react_agent(
            model=llm.bind_tools(tools, parallel_tool_calls=False), 
            tools=tools, 
            prompt=SYSTEM_PROMPT, 
            checkpointer=checkpointer
        )
        
        logger.info("Agent initialized successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise    
    


async def stream(prompt: str, session: str, user_id: str, organization_id: str):
    """Stream the agent with the given prompt and session. Returns a stream of chunks from the agent."""

    index = 0
    agent = agent_ctx.get()
    stream_handler = StreamHandler()

    start_time = datetime.now()
    logger.info(f"Started receiving streaming result at {start_time}")

    try:
        result = agent.astream(
            input={"messages": [{"role": "user", "content": prompt}]},
            config={
                "configurable": {
                    "thread_id": session, 
                    "user_id": user_id, 
                    "organization_id": organization_id
                },
                "callbacks": []  # Ensure callbacks are properly initialized
            },
            stream_mode=["updates", "messages"]
        )

        async for chunk in result:
            try:
                for processed in stream_handler.process_chunk(chunk):
                    yield f"id: {str(index)}\ndata: {processed}\n\n"
                    index += 1
            except Exception as chunk_error:
                logger.error(f"Error processing chunk {index}: {chunk_error}")
                continue
                
    except Exception as e:
        logger.error(f"Error in streaming: {e}")
        yield f"id: {index}\ndata: {{\"error\": \"Streaming error occurred\"}}\n\n"
        
    end_time = datetime.now()
    logger.info(f"Finished receiving streaming result at {end_time}. Chunks received: {index}. Time taken: {end_time - start_time}")



async def invoke(prompt: str, session: str, user_id: str, organization_id: str):
    """Invoke the agent with the given prompt and session. Returns the final response from the agent as a string."""
    
    start_time = datetime.now()
    logger.info(f"Invoke started at {start_time}")
    agent = agent_ctx.get()

    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config={
                "configurable": {
                    "thread_id": session, 
                    "user_id": user_id, 
                    "organization_id": organization_id
                },
                "callbacks": []  # Ensure callbacks are properly initialized
            }
        )

        end_time = datetime.now()
        logger.info(f"Invoke finished at {end_time}. Time taken: {end_time - start_time}")

        return {
            "message": result.get("messages")[-1].content
        }
        
    except Exception as e:
        logger.error(f"Error in invoke: {e}")
        return {
            "message": "An error occurred while processing your request. Please try again."
        }


async def resume(answers: dict, session: str, user_id: str, organization_id: str):
    """Resume the agent with the given session. Returns the final response from the agent as a string."""
    
    index = 0
    command = Command(resume={**answers})
    stream_handler = StreamHandler()
    agent = agent_ctx.get()

    start_time = datetime.now()
    logger.info(f"Started resuming agent at {start_time} with answers {answers}")

    try:
        result = agent.astream(
            input=command,
            config={
                "configurable": {
                    "thread_id": session, 
                    "user_id": user_id, 
                    "organization_id": organization_id
                },
                "callbacks": []  # Ensure callbacks are properly initialized
            },
            stream_mode=["updates", "messages"]
        )

        async for chunk in result:
            try:
                for processed in stream_handler.process_chunk(chunk):
                    yield f"id: {str(index)}\ndata: {processed}\n\n"
                    index += 1
            except Exception as chunk_error:
                logger.error(f"Error processing chunk {index} in resume: {chunk_error}")
                continue
                
    except Exception as e:
        logger.error(f"Error in resume streaming: {e}")
        yield f"id: {index}\ndata: {{\"error\": \"Resume streaming error occurred\"}}\n\n"
        
    end_time = datetime.now()
    logger.info(f"Finished receiving streaming result at {end_time}. Chunks received: {index}. Time taken: {end_time - start_time}")

