
import os
import time
import json
import logging
import random
from functools import wraps
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from openai import OpenAI
from openai import RateLimitError, APIError, APIConnectionError, APITimeoutError
import re

try:
    from pinecone.exceptions import PineconeException
except (ImportError, ModuleNotFoundError):
    # Fallback for newer pinecone versions where exceptions might be in different module
    try:
        from pinecone import PineconeException
    except (ImportError, ModuleNotFoundError):
        # Ultimate fallback
        PineconeException = Exception

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    max_retries: int = 10,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to avoid thundering herd
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (RateLimitError, APIError, APIConnectionError, APITimeoutError, 
                        PineconeException, ConnectionError, TimeoutError) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries. Last error: {e}")
                        raise last_exception
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"Function {func.__name__} failed on attempt {attempt + 1}/{max_retries + 1}. "
                                 f"Retrying in {delay:.2f} seconds. Error: {e}")
                    time.sleep(delay)
                except Exception as e:
                    # For non-retryable exceptions, fail immediately
                    logger.error(f"Function {func.__name__} failed with non-retryable error: {e}")
                    raise e
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


@retry_with_exponential_backoff(max_retries=5, base_delay=1.0, max_delay=120.0)
def create_embedding(openai_client: OpenAI, embedding_model: str, text: str) -> list[float]:
    """Generate embedding vector for a given data with retry logic and token limit handling."""
    try:
        # Clean and truncate text to fit OpenAI token limits
        cleaned_text = re.sub(r'\s+', ' ', text.strip())
        
        # text-embedding-3-small has 8192 token limit
        # Conservative estimate: 1 token ≈ 3 characters for mixed content
        max_chars = 8192 * 2.5  # About 20,480 chars to be safe
        
        if len(cleaned_text) > max_chars:
            logger.warning(f"Text too long ({len(cleaned_text)} chars), truncating to {max_chars} chars")
            cleaned_text = cleaned_text[:int(max_chars)] + "..."
        
        response = openai_client.embeddings.create(
            model=embedding_model,
            input=cleaned_text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding creation failed: {e}")
        return None

@retry_with_exponential_backoff(max_retries=3, base_delay=2.0, max_delay=60.0)
def upsert_chunk_to_pinecone(index, vectors_chunk: List[Dict[str, Any]]) -> None:
    """Upsert a chunk of vectors to Pinecone with retry logic."""
    if not vectors_chunk:
        logger.warning("No vectors to upsert in chunk")
        return
    
    # This call will be retried on failure
    index.upsert(vectors=vectors_chunk)
    logger.info(f"Successfully upserted {len(vectors_chunk)} vectors to Pinecone")


def save_progress(progress_data: dict, progress_file: str) -> None:
    """Save progress data to file."""
    try:
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
        logger.debug(f"Progress saved: {len(progress_data.get('processed_ids', []))} venues processed")
    except Exception as e:
        logger.warning(f"Could not save progress: {e}")


def load_progress(progress_file: str) -> set:
    """Load progress data from file and return set of processed IDs."""
    try:
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            processed_ids = set(progress_data.get('processed_ids', []))
            logger.info(f"Loaded progress: {len(processed_ids)} venues already processed")
            return processed_ids
        else:
            logger.info("No previous progress found, starting fresh")
            return set()
    except Exception as e:
        logger.warning(f"Could not load progress, starting fresh: {e}")
        return set()


def insert_data_in_chunks_into_pinecone(
    pinecone_client: Pinecone, 
    openai_client: OpenAI, 
    embedding_model: str, 
    index_name: str, 
    venues_data: list,
    chunk_size: int = 50,
    embedding_batch_size: int = 100,
    delay_between_chunks: float = 0.1,
    save_progress_enabled: bool = True,
    progress_file: Optional[str] = None
):
    """
    Insert venue embeddings into Pinecone in chunks with comprehensive error handling and retry logic.
    
    Args:
        pinecone_client: Initialized Pinecone client
        openai_client: Initialized OpenAI client
        embedding_model: OpenAI embedding model to use
        index_name: Name of the Pinecone index
        venues_data: List of venue dictionaries with 'context' and 'metadata' fields
        chunk_size: Number of vectors to upsert in each Pinecone batch (default: 50)
        embedding_batch_size: Number of venues to process for embeddings in each batch (default: 100)
        delay_between_chunks: Delay between Pinecone upsert chunks in seconds (default: 0.1)
        save_progress_enabled: Whether to track and save progress for resumption (default: True)
        progress_file: Custom progress file name (default: auto-generated)
    
    Returns:
        Dict with processing statistics
    """
    
    try:
        # Initialize progress tracking
        processed_ids = set()
        progress_file_name = progress_file or f"pinecone_insert_progress_{index_name}.json"
        
        # Load existing progress if enabled
        if save_progress_enabled:
            processed_ids = load_progress(progress_file_name)
        
        # Get Pinecone index
        try:
            index = pinecone_client.Index(index_name)
            logger.info(f"Connected to Pinecone index: {index_name}")
        except Exception as e:
            logger.error(f"Error connecting to Pinecone index {index_name}: {e}")
            raise
        
        # Filter out already processed venues
        unprocessed_venues = []
        for venue in venues_data:
            venue_id = str(venue.get('_id', venue.get('id', '')))
            if venue_id and venue_id not in processed_ids:
                unprocessed_venues.append(venue)
        
        total_venues = len(venues_data)
        already_processed = len(processed_ids)
        to_process = len(unprocessed_venues)
        
        logger.info(f"Total venues: {total_venues}")
        logger.info(f"Already processed: {already_processed}")
        logger.info(f"To process: {to_process}")
        
        if to_process == 0:
            logger.info("All venues already processed!")
            return {
                'total_venues': total_venues,
                'already_processed': already_processed,
                'newly_processed': 0,
                'successful_embeddings': 0,
                'successful_upserts': 0,
                'failed_embeddings': 0,
                'failed_upserts': 0
            }
        
        # Statistics tracking
        stats = {
            'total_venues': total_venues,
            'already_processed': already_processed,
            'newly_processed': 0,
            'successful_embeddings': 0,
            'successful_upserts': 0,
            'failed_embeddings': 0,
            'failed_upserts': 0
        }
        
        # Process venues in embedding batches
        for batch_start in range(0, to_process, embedding_batch_size):
            batch_end = min(batch_start + embedding_batch_size, to_process)
            current_batch = unprocessed_venues[batch_start:batch_end]
            
            logger.info(f"Processing embedding batch {batch_start//embedding_batch_size + 1}: "
                       f"venues {batch_start + 1}-{batch_end} of {to_process}")
            
            # Generate embeddings for current batch
            vectors_batch = []
            
            for venue in current_batch:
                try:
                    venue_id = str(venue.get('_id', venue.get('id', '')))
                    context = venue.get('context', '')
                    metadata = venue.get('metadata', {})
                    
                    if not venue_id:
                        logger.warning("Skipping venue without ID")
                        continue
                    
                    if not context.strip():
                        logger.warning(f"Skipping venue {venue_id} without context")
                        continue
                    
                    # Generate embedding with retry logic
                    embedding = create_embedding(openai_client, embedding_model, context)
                    
                    if embedding:
                        vectors_batch.append({
                            "id": venue_id,
                            "values": embedding,
                            "metadata": metadata
                        })
                        stats['successful_embeddings'] += 1
                        logger.debug(f"Generated embedding for venue {venue_id}")
                    else:
                        logger.error(f"Failed to generate embedding for venue {venue_id}")
                        stats['failed_embeddings'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing venue {venue.get('_id', 'unknown')}: {e}")
                    stats['failed_embeddings'] += 1
                    continue
            
            # Upsert vectors in chunks
            if vectors_batch:
                logger.info(f"Upserting {len(vectors_batch)} vectors in chunks of {chunk_size}")
                
                for chunk_start in range(0, len(vectors_batch), chunk_size):
                    chunk_end = min(chunk_start + chunk_size, len(vectors_batch))
                    vectors_chunk = vectors_batch[chunk_start:chunk_end]
                    
                    try:
                        # Upsert chunk with retry logic
                        upsert_chunk_to_pinecone(index, vectors_chunk)
                        stats['successful_upserts'] += len(vectors_chunk)
                        
                        # Track processed IDs for progress
                        for vector in vectors_chunk:
                            processed_ids.add(vector['id'])
                        
                        logger.info(f"Upserted chunk {chunk_start//chunk_size + 1}: "
                                  f"{len(vectors_chunk)} vectors")
                        
                        # Small delay between chunks to avoid rate limits
                        if delay_between_chunks > 0:
                            time.sleep(delay_between_chunks)
                            
                    except Exception as e:
                        logger.error(f"Failed to upsert chunk {chunk_start//chunk_size + 1}: {e}")
                        stats['failed_upserts'] += len(vectors_chunk)
                        continue
            
            # Update statistics
            stats['newly_processed'] = len(processed_ids) - already_processed
            
            # Save progress periodically
            if save_progress_enabled:
                progress_data = {
                    'processed_ids': list(processed_ids),
                    'last_updated': time.time(),
                    'stats': stats
                }
                save_progress(progress_data, progress_file_name)
            
            # Log batch completion
            logger.info(f"Completed embedding batch {batch_start//embedding_batch_size + 1}. "
                       f"Progress: {len(processed_ids)}/{total_venues}")
        
        # Final statistics
        logger.info("=== INSERTION COMPLETE ===")
        logger.info(f"Total venues: {stats['total_venues']}")
        logger.info(f"Already processed: {stats['already_processed']}")
        logger.info(f"Newly processed: {stats['newly_processed']}")
        logger.info(f"Successful embeddings: {stats['successful_embeddings']}")
        logger.info(f"Successful upserts: {stats['successful_upserts']}")
        logger.info(f"Failed embeddings: {stats['failed_embeddings']}")
        logger.info(f"Failed upserts: {stats['failed_upserts']}")
        
        # Clean up progress file if everything was successful
        if save_progress_enabled and stats['failed_embeddings'] == 0 and stats['failed_upserts'] == 0:
            try:
                if os.path.exists(progress_file_name):
                    os.remove(progress_file_name)
                    logger.info("Progress file cleaned up after successful completion")
            except Exception as e:
                logger.warning(f"Could not clean up progress file: {e}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Critical error in insert_data_in_chunks_into_pinecone: {e}")
        
        # Save progress even on error
        if save_progress_enabled and 'processed_ids' in locals():
            progress_data = {
                'processed_ids': list(processed_ids),
                'last_updated': time.time(),
                'error': str(e),
                'stats': stats if 'stats' in locals() else {}
            }
            progress_file_name = progress_file or f"pinecone_insert_progress_{index_name}.json"
            save_progress(progress_data, progress_file_name)
            logger.info("Progress saved before exit due to error")
        
        raise

