import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
MONGO_DB_URI = os.getenv("MONGO_DB_URI")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6378"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "test@123")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "venue-embeddings")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")

# MongoDB Collection Configuration
MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME", "telo")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "venues")

logger.info(f"MONGO_DB_URI: {MONGO_DB_URI}")
logger.info(f"Redis configured at {REDIS_HOST}:{REDIS_PORT}")
logger.info(f"Pinecone index: {PINECONE_INDEX_NAME}")