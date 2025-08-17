
from pymongo import AsyncMongoClient
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from configs.settings import MONGO_DB_URI
import logging

logger = logging.getLogger(__name__)

async def create_checkpointer():
    mongodb =  AsyncMongoClient(MONGO_DB_URI)
    checkpointer = AsyncMongoDBSaver(client=mongodb, db_name="checkpoints", checkpoint_collection_name="telo-agent",writes_collection_name="telo-agent-writes")
    return checkpointer

async def create_memory_store():
    return None
