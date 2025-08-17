from pydantic import BaseModel, Field
from langchain.tools import tool
import logging
import json

from search.embeddings import search_venues_in_rag, initialize_mongo_client
from bson import ObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SearchVenuesInput(BaseModel):
    query: str = Field(description="The query to search for venues")
    filters: dict | None = Field(None, description="Optional filters to apply to the search (e.g., location, capacity)")
    top_k: int = Field(15, description="The number of venues to return. 15-20 is recommended")
    reason: str = Field("", description="The reason for the search")
   

@tool(args_schema=SearchVenuesInput, name_or_callable="search_venues", response_format="content_and_artifact")
async def search_venues(query: str, top_k: int = 25, filters: dict | None = None, reason: str = ""):
    """
    Search for venues based on a query string, returning the top matching venues.

    Args:
        query (str): The search query describing the desired venue or event.
        top_k (int, optional): The maximum number of venues to return. Defaults to 15.
        filters (dict, optional): Additional filters to apply to the search (e.g., location, capacity).
        reason (str, optional): The reason for the search.

    Returns:
        tuple: A tuple of (content, artifact) where content is a human-readable summary and artifact is the raw search results.
    """
    # Get the raw search results
    results = search_venues_in_rag(query=query, top_k=top_k, filters=filters)
    # If search_vendors is async, await it; otherwise, just call it.
    if callable(getattr(results, "__await__", None)):
        results = await results

    # with open("venues_data.txt", "w", encoding="utf-8") as f:
    #     f.write(str(results))

    # Extract all venue IDs from the search results
    venue_ids = []
    for result in results.matches:
        venue_ids.append(result.id)
    
    logger.info(f"Extracted {len(venue_ids)} venue IDs: {venue_ids}")

    # Convert IDs to MongoDB ObjectId format and search in database
    all_venues = []
    mongo_client, database, collection = initialize_mongo_client()
    
    for venue_id in venue_ids:
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(venue_id)
            
            # Search in MongoDB
            venue_doc = collection.find_one({"_id": object_id})
            
            if venue_doc:
                # Convert ObjectId back to string for JSON serialization
                venue_doc["_id"] = str(venue_doc["_id"])
                all_venues.append(venue_doc)
                logger.info(f"Found venue in database: {venue_id}")
            else:
                logger.warning(f"Venue not found in database: {venue_id}")
                
        except Exception as e:
            logger.error(f"Error processing venue ID {venue_id}: {str(e)}")
            continue
    
    # Close MongoDB connection
    mongo_client.close()
    
    logger.info(f"Retrieved {len(all_venues)} venues from database")
    
    # Create JSON response
    response_data = {
        "query": query,
        "filters": filters,
        "total_results": len(all_venues),
        "venues": all_venues
    }
    
    # Save the detailed venue data to a JSON file
    # with open("venue_search_response.json", "w", encoding="utf-8") as f:
    #     json.dump(response_data, f, ensure_ascii=False, indent=2)
    
    logger.info("Venue search completed and saved to venue_search_response.json")
    
    return json.dumps(response_data, ensure_ascii=False, indent=2), response_data