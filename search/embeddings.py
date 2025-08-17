import os
import sys

# Add the parent directory to the Python path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import logging
from openai import OpenAI
from utils.safe_get import safe_get, safe_str, safe_int, safe_float, safe_bool, safe_list
from utils.batch_processing import insert_data_in_chunks_into_pinecone, retry_with_exponential_backoff, create_embedding
import re

def parse_currency_to_int(currency_str):
    """Parse currency string like '$13,249' to integer 13249"""
    if not currency_str:
        return 0
    
    # Convert to string if it's not already
    currency_str = str(currency_str)
    
    # Remove dollar sign, commas, and any whitespace
    cleaned = re.sub(r'[$,\s]', '', currency_str)
    
    try:
        return int(cleaned)
    except (ValueError, TypeError):
        return 0

from configs.settings import (
    OPENAI_API_KEY, 
    PINECONE_API_KEY, 
    PINECONE_INDEX_NAME, 
    PINECONE_ENVIRONMENT,
    PINECONE_CLOUD,
    MONGO_DB_URI,
    MONGO_DATABASE_NAME,
    MONGO_COLLECTION_NAME
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_mongo_client(database_name: str = None, collection_name: str = None):
    """Create clients for MongoDB."""
    # mongo client
    mongo_client = MongoClient(MONGO_DB_URI)
    database = mongo_client[database_name or MONGO_DATABASE_NAME]
    collection = database[collection_name or MONGO_COLLECTION_NAME]
    
    return mongo_client, database, collection


def initialize_pinecone_client():
    """Create a Pinecone client."""
    pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    pinecone_index_name = PINECONE_INDEX_NAME
    pinecone_cloud = PINECONE_CLOUD
    pinecone_environment = PINECONE_ENVIRONMENT
    return pinecone_client, pinecone_index_name, pinecone_cloud, pinecone_environment

def initialize_openai_client():
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    embedding_model = "text-embedding-3-small"
    embedding_dimension = 1536
    batch_size = 100
    return openai_client, embedding_model, embedding_dimension, batch_size


@retry_with_exponential_backoff(max_retries=3, base_delay=2.0, max_delay=30.0)
def create_pinecone_index(pinecone_client: Pinecone, index_name: str,region: str,  dimension: int = 1536, metric: str = "cosine", cloud: str = "aws"):
    """Create a Pinecone index with serverless specification."""
    try:
        if not pinecone_client.has_index(index_name):
            logger.info(f"Creating new Pinecone index: {index_name}")
            pinecone_client.create_index(
                name=index_name, 
                dimension=dimension, 
                metric=metric,
                spec=ServerlessSpec(
                    cloud=cloud,
                    region=region
                )
            )
            logger.info("Index created successfully")
            index = pinecone_client.Index(index_name)
            return index
        else:
            logger.info(f"Using existing Pinecone index: {index_name}")
            index = pinecone_client.Index(index_name)
            return index
    
    except Exception as e:
        logger.error(f"Error creating Pinecone index: {e}")
        raise


def extract_single_venue_fields(doc: dict):
    """Extract and process fields from a single MongoDB document for embedding."""
    try:
        venue_info = {
            '_id': safe_str(safe_get(doc, '_id')),
            'accountId': safe_str(safe_get(doc, 'accountId')),
            'isApproved': safe_bool(safe_get(doc, 'isApproved')),
            'rating': safe_float(safe_get(doc, 'rating')),
            'reviewCount': safe_int(safe_get(doc, 'reviewCount')),
            'vendorType': safe_str(safe_get(doc, 'vendorType'), max_length=100),
            'serveEvents': [e.strip().lower() for e in safe_list(safe_get(doc, 'serveEvents'))],
            'businessName': safe_str(safe_get(doc, 'businessName'), max_length=200),
            'businessDescription': safe_str(safe_get(doc, 'businessDescription'), max_length=1000),
            'businessEmail': safe_str(safe_get(doc, 'businessEmail'), max_length=100),
            'businessPhone': safe_str(safe_get(doc, 'businessPhone'), max_length=50),
            'contactPerson': safe_str(safe_get(doc, 'contactPerson'), max_length=100),
            'line_one': safe_str(safe_get(doc, 'line_one'), max_length=200),
            'line_two': safe_str(safe_get(doc, 'line_two'), max_length=200),
            'city': safe_str(safe_get(doc, 'city'), max_length=100),
            'state': safe_str(safe_get(doc, 'state'), max_length=100),
            'zip': safe_str(safe_get(doc, 'zip'), max_length=20),
            'country': safe_str(safe_get(doc, 'country'), max_length=100),
            'serviceRadius': safe_float(safe_get(doc, 'serviceRadius')),
            'leadTime': safe_int(safe_get(doc, 'leadTime')),  # keep numeric
            'responseTime': safe_int(safe_get(doc, 'responseTime')),  # keep numeric
            'serviceLanguages': [l.strip().lower() for l in safe_list(safe_get(doc, 'serviceLanguages'))],
            'accessibility': safe_str(safe_get(doc, 'accessibility'), max_length=500),
            'budgetMin': parse_currency_to_int(safe_get(doc, 'budgetMin')),
            'budgetMax': parse_currency_to_int(safe_get(doc, 'budgetMax')),
            'lat': safe_float(safe_get(doc, 'lat')),
            'lng': safe_float(safe_get(doc, 'lng'))
        }
        
        # Create combined context for embedding
        venue_info['context'] = f"""
        Business Name: {venue_info['businessName']}
        Description: {venue_info['businessDescription']}
        Location: {venue_info['line_one']} {venue_info['line_two']}, {venue_info['city']}, {venue_info['state']} {venue_info['zip']}, {venue_info['country']}
        Events Served: {', '.join(venue_info['serveEvents'])}
        Service Radius: {venue_info['serviceRadius']} km
        Languages: {', '.join(venue_info['serviceLanguages'])}
        Accessibility: {venue_info['accessibility']}
        Rating: {venue_info['rating']} (from {venue_info['reviewCount']} reviews)
        Contact: {venue_info['businessEmail']} | {venue_info['businessPhone']}
        Budget: ${venue_info['budgetMin']} - ${venue_info['budgetMax']}
        """.replace("\n", " ").strip()

        # Add metadata for filtering
        venue_info['metadata'] = {
            "businessName": venue_info['businessName'],
            "city": venue_info['city'],
            "state": venue_info['state'],
            "vendorType": venue_info['vendorType'],
            "serveEvents": venue_info['serveEvents'],
            "rating": venue_info['rating'],
            "isApproved": venue_info['isApproved'],
            "lat": venue_info['lat'],
            "lng": venue_info['lng'],
            "serviceRadius": venue_info['serviceRadius'],
            "leadTime": venue_info['leadTime'],
            "responseTime": venue_info['responseTime'],
            "context": venue_info['context'],  # Add the rich context for search results
            "businessDescription": venue_info['businessDescription'],
            "businessEmail": venue_info['businessEmail'],
            "businessPhone": venue_info['businessPhone'],
            "contactPerson": venue_info['contactPerson'],
            "address": f"{venue_info['line_one']} {venue_info['line_two']}, {venue_info['city']}, {venue_info['state']} {venue_info['zip']}, {venue_info['country']}".strip(),
            "serviceLanguages": venue_info['serviceLanguages'],
            "accessibility": venue_info['accessibility'],
            "reviewCount": venue_info['reviewCount'],
            "budgetMin": venue_info['budgetMin'],
            "budgetMax": venue_info['budgetMax']
        }

        # Validate essential fields
        if not venue_info['_id'] or not venue_info['businessName']:
            logger.warning(f"Incomplete doc: ID={venue_info['_id']}, Name={venue_info['businessName']}")
            return None
            
        return venue_info

    except Exception as doc_error:
        logger.warning(f"Error processing doc {safe_get(doc, '_id', 'unknown')}: {doc_error}")
        return None


def extract_fields_from_mongo_db(mongo_client: MongoClient, database: str, collection: str):
    """Extract Venues information from MongoDB and creates the necessary fields for embedding."""
    try:
        db = mongo_client[database]
        coll = db[collection]
        
        documents = []
        logger.info("Starting document extraction from MongoDB...")
        
        for doc in coll.find():
            venue_info = extract_single_venue_fields(doc)
            if venue_info:
                documents.append(venue_info)
        
        logger.info(f"Extracted {len(documents)} valid venues")
        return documents

    except Exception as e:
        logger.error(f"Mongo extraction error: {e}")
        raise


@retry_with_exponential_backoff(max_retries=3, base_delay=1.0, max_delay=30.0)
def insert_data_into_pinecone(pinecone_client: Pinecone, openai_client: OpenAI, embedding_model: str, index_name: str, venues_data: list):
    """Insert venue embeddings into Pinecone."""
    index = pinecone_client.Index(index_name)
    vectors = []

    for venue in venues_data:
        embedding = create_embedding(openai_client, embedding_model, venue['context'])
        if embedding:
            vectors.append({
                "id": venue["_id"],
                "values": embedding,
                "metadata": venue["metadata"]
            })
    
    if vectors:
        index.upsert(vectors=vectors)
        logger.info(f"Inserted {len(vectors)} venue vectors into Pinecone")
    else:
        logger.warning("No vectors to insert into Pinecone")


@retry_with_exponential_backoff(max_retries=3, base_delay=1.0, max_delay=30.0)
def search_venues_in_pinecone(pinecone_client: Pinecone, index_name: str, query: str, top_k: int = 10, filters: dict = None):
    """Search venues in Pinecone.
    Args:
        pinecone_client: Pinecone client
        index_name: Pinecone index name
        query: Search query
        top_k: Number of results to return
        filters: Filters to apply to the search
    """
    openai_client, embedding_model, embedding_dimension, batch_size = initialize_openai_client()

    index = pinecone_client.Index(index_name)
    query_vector = create_embedding(openai_client, embedding_model, query)
    
    if not query_vector:
        logger.error("Failed to create query vector")
        return None
    
    query_results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter=filters
    )
    return query_results


def delete_data_from_pinecone(pinecone_client: Pinecone, index_name: str, ids: List[str]):
    """Delete data from Pinecone."""
    index = pinecone_client.Index(index_name)
    index.delete(ids=ids)
    logger.info(f"Deleted {len(ids)} venue vectors from Pinecone")

def update_data_in_pinecone(pinecone_client: Pinecone, index_name: str, ids: List[str], data: Dict[str, Any]):
    """Update data in Pinecone."""
    index = pinecone_client.Index(index_name)
    index.upsert(vectors=data)
    logger.info(f"Updated {len(ids)} venue vectors in Pinecone")

def process_venues_from_mongodb_to_pinecone(
    database_name: str = None, 
    collection_name: str = None,
    chunk_size: int = 50,
    embedding_batch_size: int = 100,
    use_chunked_insert: bool = True,
    is_watching: bool = False
):
    """
    Complete pipeline to process venues from MongoDB and insert into Pinecone.
    
    Args:
        database_name: MongoDB database name
        collection_name: MongoDB collection name
        chunk_size: Pinecone upsert chunk size
        embedding_batch_size: Embedding processing batch size
        use_chunked_insert: Whether to use chunked insertion with retry logic
        is_watching: Whether to watch for changes in MongoDB or directly insert data into Pinecone by fetching all data from MongoDB
    """
    try:
        # Initialize clients
        logger.info("Initializing clients...")
        mongo_client, database, collection = initialize_mongo_client()
        pinecone_client, index_name, pinecone_cloud, pinecone_environment = initialize_pinecone_client()
        openai_client, embedding_model, embedding_dimension, batch_size = initialize_openai_client()

        print(f"mongo_client: {mongo_client}")
        print(f"database: {database.name}")
        print(f"collection: {collection.name}")
        print(f"pinecone_client: {pinecone_client}")
        print(f"index_name: {index_name}")
        print(f"pinecone_cloud: {pinecone_cloud}")
        print(f"pinecone_environment: {pinecone_environment}")
        
        # Create or get Pinecone index
        logger.info("Setting up Pinecone index...")
        index = create_pinecone_index(pinecone_client= pinecone_client, index_name=index_name, region=pinecone_environment, dimension=embedding_dimension, cloud=pinecone_cloud)

        if is_watching:
           pass
        else:
            # Directly insert data into Pinecone by fetching all data from MongoDB
            logger.info("Directly inserting data into Pinecone by fetching all data from MongoDB...")
            venues_data = extract_fields_from_mongo_db(mongo_client, database.name, collection.name)
        
        if not venues_data:
            logger.warning("No venue data extracted from MongoDB")
            return
        
        # Insert data into Pinecone
        logger.info(f"Inserting {len(venues_data)} venues into Pinecone...")
        
        if use_chunked_insert:
            # Use chunked insertion with retry logic and progress tracking
            stats = insert_data_in_chunks_into_pinecone(
                pinecone_client=pinecone_client,
                openai_client=openai_client,
                embedding_model=embedding_model,
                index_name=index_name,
                venues_data=venues_data,
                chunk_size=chunk_size,
                embedding_batch_size=embedding_batch_size
            )
            
            logger.info("=== FINAL RESULTS ===")
            logger.info(f"Successfully processed {stats['newly_processed']} new venues")
            logger.info(f"Total embeddings created: {stats['successful_embeddings']}")
            logger.info(f"Total vectors upserted: {stats['successful_upserts']}")
            
            if stats['failed_embeddings'] > 0 or stats['failed_upserts'] > 0:
                logger.warning(f"Failed embeddings: {stats['failed_embeddings']}")
                logger.warning(f"Failed upserts: {stats['failed_upserts']}")
        else:
            # Use original simple insertion
            insert_data_into_pinecone(pinecone_client, openai_client, embedding_model, index_name, venues_data)
        
        # Close MongoDB connection
        mongo_client.close()
        logger.info("MongoDB connection closed")
        
    except Exception as e:
        logger.error(f"Error in complete pipeline: {e}")
        raise


def search_venues_in_rag(query: str, top_k: int = 10, filters: dict = None):
    """Search venues in RAG."""
    pinecone_client, index_name, _, _ = initialize_pinecone_client()
    results = search_venues_in_pinecone(pinecone_client=pinecone_client, index_name=index_name, query=query, top_k=top_k, filters=filters)
    return results

def search_venues_in_database(objId: str):
    """Search venues in database."""
    mongo_client, database, collection = initialize_mongo_client()
    results = mongo_client[database][collection].find({"_id": objId})
    return results

def main():
    try:
        process_venues_from_mongodb_to_pinecone(
            chunk_size=30,  
            embedding_batch_size=50,  
            use_chunked_insert=True, 
            is_watching=False
        )
        logger.info("Venue processing completed using VenueEmbeddingsProcessor")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print("\n🔄 Don't worry! You can restart the script and it will resume from where it left off")
        print("   The progress is automatically saved and will be restored on restart.")

def test_search():
    """Test the search functionality."""
    try:
        logger.info("Testing search functionality...")
        
        pinecone_client, index_name, _, _ = initialize_pinecone_client()
        
        # Test search
        results = search_venues_in_pinecone(
            pinecone_client=pinecone_client,
            index_name=index_name,
            query="wedding venue in Boston under maxBudget $50000 with catering for 150 guests for wedding",
            top_k=5,
            filters={"isApproved": True}
        )
        
        if results and results.matches:
            logger.info(f"Found {len(results.matches)} results:")
            for i, match in enumerate(results.matches, 1):
                metadata = match.metadata
                logger.info(f"{i}. {metadata.get('businessName', 'Unknown')} "
                           f"(Score: {match.score:.4f}, "
                           f"City: {metadata.get('city', 'Unknown')}, "
                           f"Rating: {metadata.get('rating', 'N/A')})"
                           f"Budget: {metadata.get('budgetMin', 'N/A')} - {metadata.get('budgetMax', 'N/A')}"
                          f"Service Languages: {metadata.get('serviceLanguages', 'N/A')}, "
                          f"Events Served: {metadata.get('serveEvents', 'N/A')}, "
                          f"Capacity Info: {metadata.get('businessDescription', 'N/A')}, "
                          f"Address: {metadata.get('address', 'N/A')}, "
                          f"Contact: {metadata.get('businessEmail', 'N/A')} | {metadata.get('businessPhone', 'N/A')}")
        else:
            logger.info("No results found")
            
    except Exception as e:
        logger.error(f"Error in search test: {e}")


if __name__ == "__main__":
    main()
    test_search()
