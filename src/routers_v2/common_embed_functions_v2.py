# Common Embed Functions V2 - OpenAI file upload and vector store operations
# Used by crawler.py for embedding files into vector stores

import asyncio, time
from typing import Optional

from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN


# ----------------------------------------- START: File Operations ----------------------------------------------------

async def upload_file_to_openai(client, filepath: str, purpose: str = "assistants") -> tuple[str, str]:
  """
  Upload a file to OpenAI.
  
  Args:
    client: OpenAI async client
    filepath: Local filesystem path to the file
    purpose: Purpose of the file (default "assistants")
    
  Returns:
    (openai_file_id, error_message) - file_id is empty string on error
  """
  try:
    with open(filepath, 'rb') as f:
      file_obj = await client.files.create(file=f, purpose=purpose)
    return file_obj.id, ""
  except Exception as e:
    return "", str(e)

async def delete_file_from_openai(client, file_id: str) -> tuple[bool, str]:
  """
  Delete a file from OpenAI.
  
  Args:
    client: OpenAI async client
    file_id: OpenAI file ID to delete
    
  Returns:
    (success, error_message)
  """
  try:
    await client.files.delete(file_id)
    return True, ""
  except Exception as e:
    return False, str(e)

# ----------------------------------------- END: File Operations ------------------------------------------------------


# ----------------------------------------- START: Vector Store Operations --------------------------------------------

async def add_file_to_vector_store(client, vector_store_id: str, file_id: str) -> tuple[bool, str]:
  """
  Add a file to a vector store.
  
  Args:
    client: OpenAI async client
    vector_store_id: Target vector store ID
    file_id: OpenAI file ID to add
    
  Returns:
    (success, error_message)
  """
  try:
    await client.vector_stores.files.create(vector_store_id=vector_store_id, file_id=file_id)
    return True, ""
  except Exception as e:
    return False, str(e)

async def remove_file_from_vector_store(client, vector_store_id: str, file_id: str) -> tuple[bool, str]:
  """
  Remove a file from a vector store.
  
  Args:
    client: OpenAI async client
    vector_store_id: Vector store ID
    file_id: OpenAI file ID to remove
    
  Returns:
    (success, error_message)
  """
  try:
    await client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file_id)
    return True, ""
  except Exception as e:
    return False, str(e)

async def list_vector_store_files(client, vector_store_id: str) -> list:
  """
  List all files in a vector store.
  
  Args:
    client: OpenAI async client
    vector_store_id: Vector store ID
    
  Returns:
    List of file objects with id, status, etc.
  """
  result = []
  try:
    async for file in client.vector_stores.files.list(vector_store_id=vector_store_id):
      result.append({
        "id": getattr(file, 'id', ''),
        "status": getattr(file, 'status', ''),
        "created_at": getattr(file, 'created_at', 0),
        "vector_store_id": getattr(file, 'vector_store_id', '')
      })
  except Exception:
    pass
  return result

async def wait_for_vector_store_ready(client, vector_store_id: str, file_ids: list, timeout_seconds: int = 300) -> list:
  """
  Poll until all files have status != 'in_progress'.
  
  Args:
    client: OpenAI async client
    vector_store_id: Vector store ID
    file_ids: List of file IDs to wait for
    timeout_seconds: Maximum time to wait (default 300s)
    
  Returns:
    List of file statuses with {id, status}
  """
  if not file_ids: return []
  
  file_ids_set = set(file_ids)
  start_time = time.time()
  
  while True:
    elapsed = time.time() - start_time
    if elapsed >= timeout_seconds: break
    
    all_files = await list_vector_store_files(client, vector_store_id)
    target_files = [f for f in all_files if f.get('id') in file_ids_set]
    
    in_progress = [f for f in target_files if f.get('status') == 'in_progress']
    if not in_progress:
      return target_files
    
    await asyncio.sleep(2)
  
  # Timeout reached, return current state
  all_files = await list_vector_store_files(client, vector_store_id)
  return [f for f in all_files if f.get('id') in file_ids_set]

async def get_failed_embeddings(client, vector_store_id: str, file_ids: list) -> list:
  """
  Get files where embedding status != 'completed'.
  
  Args:
    client: OpenAI async client
    vector_store_id: Vector store ID
    file_ids: List of file IDs to check
    
  Returns:
    List of file objects where status != 'completed'
  """
  if not file_ids: return []
  
  file_ids_set = set(file_ids)
  all_files = await list_vector_store_files(client, vector_store_id)
  failed = [f for f in all_files if f.get('id') in file_ids_set and f.get('status') != 'completed']
  return failed

# ----------------------------------------- END: Vector Store Operations ----------------------------------------------


# ----------------------------------------- START: Batch Operations ---------------------------------------------------

async def upload_and_embed_file(client, vector_store_id: str, filepath: str, logger: Optional[MiddlewareLogger] = None) -> tuple[str, str]:
  """
  Upload a file to OpenAI and add it to a vector store in one operation.
  
  Args:
    client: OpenAI async client
    vector_store_id: Target vector store ID
    filepath: Local filesystem path to the file
    logger: Optional logger
    
  Returns:
    (openai_file_id, error_message) - file_id is empty string on error
  """
  # Upload file
  file_id, upload_error = await upload_file_to_openai(client, filepath)
  if upload_error:
    if logger: logger.log_function_output(f"  ERROR: Upload failed: {upload_error}")
    return "", f"Upload failed: {upload_error}"
  
  # Add to vector store
  success, add_error = await add_file_to_vector_store(client, vector_store_id, file_id)
  if not success:
    # Cleanup: delete the uploaded file
    await delete_file_from_openai(client, file_id)
    if logger: logger.log_function_output(f"  ERROR: Add to vector store failed: {add_error}")
    return "", f"Add to vector store failed: {add_error}"
  
  return file_id, ""

async def remove_and_delete_file(client, vector_store_id: str, file_id: str, logger: Optional[MiddlewareLogger] = None) -> tuple[bool, str]:
  """
  Remove a file from a vector store and delete it from OpenAI.
  
  Args:
    client: OpenAI async client
    vector_store_id: Vector store ID
    file_id: OpenAI file ID
    logger: Optional logger
    
  Returns:
    (success, error_message)
  """
  errors = []
  
  # Remove from vector store
  success, error = await remove_file_from_vector_store(client, vector_store_id, file_id)
  if not success:
    errors.append(f"Remove from VS: {error}")
    if logger: logger.log_function_output(f"  WARNING: Could not remove from vector store: {error}")
  
  # Delete file
  success, error = await delete_file_from_openai(client, file_id)
  if not success:
    errors.append(f"Delete file: {error}")
    if logger: logger.log_function_output(f"  WARNING: Could not delete file: {error}")
  
  if errors:
    return False, "; ".join(errors)
  return True, ""

# ----------------------------------------- END: Batch Operations -----------------------------------------------------
