# Common Open AI functions (COAI) V2
# Copyright 2025, Karsten Held (MIT License)
# V2 version using MiddlewareLogger

import datetime, os, time, asyncio
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional, Union

from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity import ClientSecretCredential as SyncClientSecretCredential, DefaultAzureCredential as SyncDefaultAzureCredential, get_bearer_token_provider as sync_get_bearer_token_provider
from azure.identity.aio import ClientSecretCredential, DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai._types import Body, Headers, NOT_GIVEN, NotGiven, Query
from openai.types.responses import ResponseInputParam, ResponseTextConfigParam, ToolParam, response_create_params
from openai.types.responses.response_includable import ResponseIncludable
from openai.types.responses.response_prompt_param import ResponsePromptParam
from openai.types.shared_params.metadata import Metadata
from openai.types.shared_params.reasoning import Reasoning
from openai.types.shared_params.responses_model import ResponsesModel

import httpx

from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN

# Global variable for OpenAI datetime attributes that need conversion
OPENAI_DATETIME_ATTRIBUTES = ["created_at", "expires_at"]

# Replicate OpenAI Vector Store Search Response types
# https://github.com/openai/openai-python/blob/main/src/openai/types/vector_store_search_response.py
@dataclass
class CoaiSearchContent:
  text: str
  type: Literal["text"]

@dataclass
class CoaiSearchResults:
  content: List[CoaiSearchContent]
  file_id: str
  filename: str
  score: float
  # Set of 16 key-value pairs that can be attached to an object.
  attributes: Optional[Dict[str, Union[str, float, bool]]] = None

@dataclass
class CoaiSearchParams:
  query: str
  max_num_results: int
  score_threshold: float = 0.001
  filters: Optional[Dict[str, Union[str, float, bool]]] = None
  rewrite_query: bool = False

# Copy the needed parameters from create() function (current version: 1.101.0):
# https://github.com/openai/openai-python/blob/main/src/openai/resources/responses/responses.py
@dataclass
class CoaiResponseParams:
  input: Union[str, ResponseInputParam] | NotGiven = NOT_GIVEN
  model: ResponsesModel | NotGiven = NOT_GIVEN
  background: Optional[bool] | NotGiven = NOT_GIVEN
  conversation: Optional[response_create_params.Conversation] | NotGiven = NOT_GIVEN
  include: Optional[List[ResponseIncludable]] | NotGiven = NOT_GIVEN
  instructions: Optional[str] | NotGiven = NOT_GIVEN
  max_output_tokens: Optional[int] | NotGiven = NOT_GIVEN
  max_tool_calls: Optional[int] | NotGiven = NOT_GIVEN
  metadata: Optional[Metadata] | NotGiven = NOT_GIVEN
  parallel_tool_calls: Optional[bool] | NotGiven = NOT_GIVEN
  previous_response_id: Optional[str] | NotGiven = NOT_GIVEN
  prompt: Optional[ResponsePromptParam] | NotGiven = NOT_GIVEN
  prompt_cache_key: str | NotGiven = NOT_GIVEN
  reasoning: Optional[Reasoning] | NotGiven = NOT_GIVEN
  safety_identifier: str | NotGiven = NOT_GIVEN
  service_tier: Optional[Literal["auto", "default", "flex", "scale", "priority"]] | NotGiven = NOT_GIVEN
  store: Optional[bool] | NotGiven = NOT_GIVEN
  stream: Optional[Literal[False]] | NotGiven = NOT_GIVEN
  stream_options: Optional[response_create_params.StreamOptions] | NotGiven = NOT_GIVEN
  temperature: Optional[float] | NotGiven = NOT_GIVEN
  text: ResponseTextConfigParam | NotGiven = NOT_GIVEN
  tool_choice: response_create_params.ToolChoice | NotGiven = NOT_GIVEN
  tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN
  top_logprobs: Optional[int] | NotGiven = NOT_GIVEN
  top_p: Optional[float] | NotGiven = NOT_GIVEN
  truncation: Optional[Literal["auto", "disabled"]] | NotGiven = NOT_GIVEN
  user: str | NotGiven = NOT_GIVEN
  # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
  # The extra values given here take precedence over values defined on the client or passed to this method.
  extra_headers: Headers | None = None
  extra_query: Query | None = None
  extra_body: Body | None = None
  timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN

# Replicate OpenAI Vector Store types
# https://github.com/openai/openai-python/blob/main/src/openai/types/vector_store.py
@dataclass
class CoaiFileCounts:
  cancelled: int
  completed: int
  failed: int
  in_progress: int
  total: int

@dataclass
class CoaiExpiresAfter:
  anchor: Literal["last_active_at"]
  days: int

@dataclass
class CoaiVectorStore:
  id: str
  created_at: int
  file_counts: CoaiFileCounts
  name: str
  status: Literal["expired", "in_progress", "completed"]
  usage_bytes: int
  last_active_at: Optional[int] = None
  expires_after: Optional[CoaiExpiresAfter] = None
  expires_at: Optional[int] = None
  # Set of 16 key-value pairs that can be attached to an object.
  metadata: Optional[Dict[str, Union[str, float, bool]]] = None

# Replicate OpenAI File types
# https://github.com/openai/openai-python/blob/main/src/openai/types/file_object.py
@dataclass
class CoaiFile:
  id: str
  bytes: int
  created_at: int
  filename: str
  purpose: Literal["assistants", "assistants_output", "batch", "batch_output", "fine-tune", "fine-tune-results", "vision", "user_data"]
  status: Literal["uploaded", "processed", "error"]
  expires_at: Optional[int] = None
  status_details: Optional[str] = None

# Replicate OpenAI Vector Store File types
# https://github.com/openai/openai-python/blob/main/src/openai/types/vector_stores/vector_store_file.py
@dataclass
class CoaiLastError:
  code: Literal["server_error", "unsupported_file", "invalid_file"]
  message: str

# Replicate OpenAI Vector Store File types
# https://github.com/openai/openai-python/blob/main/src/openai/types/vector_stores/vector_store_file.py
@dataclass
class CoaiVectorStoreFile:
  id: str
  created_at: int
  status: Literal["in_progress", "completed", "cancelled", "failed"]
  usage_bytes: int
  vector_store_id: str
  # added from CoaiFile
  filename: str
  purpose: Literal["assistants", "assistants_output", "batch", "batch_output", "fine-tune", "fine-tune-results", "vision", "user_data"]
  global_status: Literal["uploaded", "processed", "error"]
  last_error: Optional[CoaiLastError] = None
  attributes: Optional[Dict[str, Union[str, float, bool]]] = None
  chunking_strategy: Optional[Dict[str, any]] = None
  expires_at: Optional[int] = None
  status_details: Optional[str] = None


# Replicate OpenAI Assistant types
# https://github.com/openai/openai-python/blob/main/src/openai/types/beta/assistant.py
@dataclass
class CoaiToolResourcesCodeInterpreter:
  file_ids: Optional[List[str]] = None

@dataclass
class CoaiToolResourcesFileSearch:
  vector_store_ids: Optional[List[str]] = None

@dataclass
class CoaiToolResources:
  code_interpreter: Optional[CoaiToolResourcesCodeInterpreter] = None
  file_search: Optional[CoaiToolResourcesFileSearch] = None

@dataclass
class CoaiAssistant:
  id: str
  created_at: int
  model: str
  name: Optional[str] = None
  description: Optional[str] = None
  instructions: Optional[str] = None
  tools: Optional[List[Dict]] = None
  tool_resources: Optional[CoaiToolResources] = None
  temperature: Optional[float] = None
  top_p: Optional[float] = None
  response_format: Optional[Dict] = None
  # Set of 16 key-value pairs that can be attached to an object.
  metadata: Optional[Dict[str, Union[str, float, bool]]] = None

def create_async_openai_client(api_key) -> AsyncOpenAI:
  if not api_key: raise ValueError("OPENAI_API_KEY is required when OPENAI_SERVICE_TYPE is set to 'openai'")
  return AsyncOpenAI(api_key=api_key)

# Create an async Azure OpenAI client using API key authentication
def create_async_azure_openai_client_with_api_key(endpoint, api_version, api_key) -> AsyncAzureOpenAI:
  if not (endpoint and api_key): raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are required for Azure OpenAI key authentication")
  return AsyncAzureOpenAI(api_version=api_version, azure_endpoint=endpoint, api_key=api_key)

# Create an async Azure OpenAI client with any AsyncTokenCredential
# ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
# DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
def create_async_azure_openai_client_with_credential(endpoint, api_version, credential: AsyncTokenCredential) -> AsyncAzureOpenAI:
  if not endpoint: raise ValueError("AZURE_OPENAI_ENDPOINT is required for Azure OpenAI credential authentication")
  token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
  return AsyncAzureOpenAI(api_version=api_version, azure_endpoint=endpoint, azure_ad_token_provider=token_provider, max_retries=5)

# Retries the given function on rate limit errors
def retry_on_openai_rate_limit_errors_for_sync_client(fn, logger: Optional[MiddlewareLogger] = None, retries=5, backoff_seconds=10):
  for attempt in range(retries):
    try:
      return fn()
    except Exception as e:
      if not (hasattr(e, 'type') and e.type == 'rate_limit_error'): raise e
      if attempt == retries - 1: raise e
      if logger: logger.log_function_output(f"Rate limit reached, retrying in {backoff_seconds} seconds... (attempt {attempt + 2} of {retries})")
      time.sleep(backoff_seconds)

def convert_openai_timestamps_to_utc(data, logger: Optional[MiddlewareLogger] = None):
  """Convert OpenAI timestamp attributes to UTC datetime strings in JSON data."""
  if isinstance(data, dict):
    for key, value in data.items():
      if key in OPENAI_DATETIME_ATTRIBUTES and value is not None:
        try: 
          converted_value = datetime.datetime.fromtimestamp(float(value)).isoformat()
          data[key] = converted_value
        except Exception as e:
          data[key] = str(value)
          if logger: logger.log_function_output(f"Failed to convert timestamp {key}: {value} -> {str(e)}")
      elif isinstance(value, dict):
        convert_openai_timestamps_to_utc(value, logger)
      elif isinstance(value, list):
        for item in value:
          if isinstance(item, dict): convert_openai_timestamps_to_utc(item, logger)
  return data


# Uses the file_search tool of the Responses API to get search results from a vector store
# Why? As of 2025-09-08, Azure Open AI Services does not support the Search API. This is a temporary workaround to get similar results.
# -> Client error '404 Resource Not Found' for url 'https://<ai-resource>.cognitiveservices.azure.com/openai/vector_stores/<VECTOR-STORE-ID>/search?api-version=2025-04-01-preview'
# https://platform.openai.com/docs/guides/tools-file-search
# https://github.com/openai/openai-python/blob/main/src/openai/resources/responses/responses.py
async def get_search_results_using_responses_api(openai_client, search_params: CoaiSearchParams, vector_store_id: str, model: str, instructions: str) -> tuple[List[CoaiSearchResults], any]:
  # Apply instructions before and after query as they are frequently ignored in OpenAI Responses
  enhanced_query = f"INSTRUCTIONS: {instructions}\n\n---\n\n{search_params.query}\n\n---\n\nINSTRUCTIONS: {instructions}"

  # Prepare file_search tool configuration
  file_search_tool = {
    "type": "file_search",
    "vector_store_ids": [vector_store_id],
    "max_num_results": search_params.max_num_results,
    "ranking_options": {"ranker": "auto", "score_threshold": search_params.score_threshold}
  }
  
  # Add filters if provided
  if search_params.filters: file_search_tool["filters"] = search_params.filters
  
  # Note: rewrite_query is not supported in Responses API file_search tool, only in vector store search API
  
  # Prepare request parameters with default temperature
  request_params = {
    "model": model,
    "input": enhanced_query,
    "tools": [file_search_tool],
    "temperature": 0,
    "include": ["file_search_call.results"]
  }
  
  # Remove temperature for reasoning models that don't support it
  remove_temperature_from_request_params_for_reasoning_models(request_params, model, reasoning_effort="minimal")

  response = await openai_client.responses.create(**request_params)

  search_results: List[CoaiSearchResults] = []
  file_search_call = next((item for item in response.output if item.type == 'file_search_call'), None)
  file_search_call_results = None if file_search_call is None else getattr(file_search_call, 'results', None)
  if  file_search_call_results:
    for result in file_search_call_results:
        content = [CoaiSearchContent(text=result.text, type="text")]
        item = CoaiSearchResults(attributes=result.attributes, content=content, file_id=result.file_id, filename=result.filename, score=result.score)
        search_results.append(item)
  return search_results, response

# Uses the Search API to get search results from a vector store (preferred method when available)
async def get_search_results_using_search_api(openai_client, search_params: CoaiSearchParams, vector_store_id: str) -> tuple[List[CoaiSearchResults], any]:
  api_search_params = {
    "vector_store_id": vector_store_id,
    "query": search_params.query,
    "ranking_options": {"ranker": "auto", "score_threshold": search_params.score_threshold},
    "max_num_results": search_params.max_num_results
  }
  
  if search_params.filters: api_search_params["filters"] = search_params.filters
  if search_params.rewrite_query: api_search_params["rewrite_query"] = True
  
  search_response = await openai_client.vector_stores.search(**api_search_params)
  
  search_results: List[CoaiSearchResults] = []
  if search_response.data:
    for result in search_response.data:
      content = [CoaiSearchContent(text=content_item.text, type=content_item.type) for content_item in result.content]
      item = CoaiSearchResults(attributes=result.attributes, content=content, file_id=result.file_id, filename=result.filename, score=result.score)
      search_results.append(item)
  
  # Create a compatible response object that matches the Responses API structure
  class SearchApiResponse:
    def __init__(self):
      self.output_text = ""  # Search API doesn't generate text, only finds content
      self.status = "completed"
      self.tool_choice = "file_search"
      # Create mock usage stats
      class MockUsage:
        input_tokens = 0
        output_tokens = 0
      self.usage = MockUsage()
  
  compatible_response = SearchApiResponse()
  return search_results, compatible_response

# Tries to get the vector store by id and returns None if it fails
async def try_get_vector_store_by_id(client, vsid) -> Optional[CoaiVectorStore]:
  try:
    vector_store = await client.vector_stores.retrieve(vsid)
    return _convert_to_coai_vector_store(vector_store)
  except Exception as e:
    return None

# Utility function to remove temperature parameter for reasoning models that don't support it
# When reasoning model is used, it will add the reasoning effort if specified
def remove_temperature_from_request_params_for_reasoning_models(request_params, model_name, reasoning_effort=None) -> None:
  if (model_name.startswith('o') or model_name.startswith('gpt-5')) and 'temperature' in request_params:
    del request_params['temperature']
  
  # Add reasoning parameter for reasoning models if reasoning_effort is specified
  if reasoning_effort and reasoning_effort in ["minimal", "low", "medium", "high"]:
    if model_name.startswith('o') or model_name.startswith('gpt-5'):
      # For 'o' models, 'minimal' is invalid and will be mapped to 'low'
      if model_name.startswith('o') and reasoning_effort == "minimal": request_params["reasoning"] = {"effort": "low"}
      else: request_params["reasoning"] = {"effort": reasoning_effort}

# ----------------------------------------------------- START: Vector stores --------------------------------------------------

def _convert_to_coai_vector_store(vector_store) -> CoaiVectorStore:
  """Convert OpenAI VectorStore to CoaiVectorStore dataclass."""
  return CoaiVectorStore(
    id=vector_store.id,
    created_at=vector_store.created_at,
    file_counts=CoaiFileCounts(
      cancelled=vector_store.file_counts.cancelled,
      completed=vector_store.file_counts.completed,
      failed=vector_store.file_counts.failed,
      in_progress=vector_store.file_counts.in_progress,
      total=vector_store.file_counts.total
    ),
    name=vector_store.name,
    status=vector_store.status,
    usage_bytes=vector_store.usage_bytes,
    last_active_at=vector_store.last_active_at,
    metadata=vector_store.metadata,
    expires_after=CoaiExpiresAfter(anchor=vector_store.expires_after.anchor, days=vector_store.expires_after.days) if vector_store.expires_after else None,
    expires_at=vector_store.expires_at
  )

def _convert_to_coai_file(file) -> CoaiFile:
  """Convert OpenAI File to CoaiFile dataclass."""
  return CoaiFile(
    id=file.id,
    bytes=file.bytes,
    created_at=file.created_at,
    filename=file.filename,
    purpose=file.purpose,
    status=file.status,
    expires_at=file.expires_at,
    status_details=file.status_details
  )

def _convert_to_coai_vector_store_file(vs_file, global_file: Optional[CoaiFile] = None) -> CoaiVectorStoreFile:
  """Convert OpenAI VectorStoreFile to CoaiVectorStoreFile dataclass with optional global file metadata."""
  # Convert last_error if present
  last_error = None
  if hasattr(vs_file, 'last_error') and vs_file.last_error:
    last_error = CoaiLastError(
      code=vs_file.last_error.code,
      message=vs_file.last_error.message
    )
  
  return CoaiVectorStoreFile(
    id=vs_file.id,
    created_at=vs_file.created_at,
    status=vs_file.status,
    usage_bytes=vs_file.usage_bytes,
    vector_store_id=vs_file.vector_store_id,
    last_error=last_error,
    attributes=getattr(vs_file, 'attributes', None),
    chunking_strategy=getattr(vs_file, 'chunking_strategy', None),
    # Add global file metadata
    filename=global_file.filename if global_file else '',
    purpose=global_file.purpose if global_file else 'assistants',
    global_status=global_file.status if global_file else 'uploaded',
    expires_at=global_file.expires_at if global_file else None,
    status_details=global_file.status_details if global_file else None
  )

def _convert_to_coai_assistant(assistant) -> CoaiAssistant:
  """Convert OpenAI Assistant to CoaiAssistant dataclass."""
  # Convert tool_resources if present
  tool_resources = None
  if assistant.tool_resources:
    code_interpreter = None
    if assistant.tool_resources.code_interpreter:
      file_ids = getattr(assistant.tool_resources.code_interpreter, 'file_ids', None) or []
      code_interpreter = CoaiToolResourcesCodeInterpreter(file_ids=file_ids)
    
    file_search = None
    if assistant.tool_resources.file_search:
      vector_store_ids = getattr(assistant.tool_resources.file_search, 'vector_store_ids', None) or []
      file_search = CoaiToolResourcesFileSearch(vector_store_ids=vector_store_ids)
    
    tool_resources = CoaiToolResources(code_interpreter=code_interpreter, file_search=file_search)
  
  # Convert tools to dict format
  tools_list = None
  if assistant.tools:
    tools_list = []
    for tool in assistant.tools:
      if hasattr(tool, 'model_dump'):
        tools_list.append(tool.model_dump())
      elif hasattr(tool, '__dict__'):
        tools_list.append(tool.__dict__)
      else:
        tools_list.append({"type": str(tool)})
  
  # Convert response_format to dict format
  response_format_dict = None
  if assistant.response_format:
    if hasattr(assistant.response_format, 'model_dump'):
      response_format_dict = assistant.response_format.model_dump()
    elif hasattr(assistant.response_format, '__dict__'):
      response_format_dict = assistant.response_format.__dict__
    else:
      response_format_dict = {"format": str(assistant.response_format)}
  
  return CoaiAssistant(
    id=assistant.id,
    created_at=assistant.created_at,
    model=assistant.model,
    name=assistant.name,
    description=assistant.description,
    instructions=assistant.instructions,
    tools=tools_list,
    tool_resources=tool_resources,
    temperature=assistant.temperature,
    top_p=assistant.top_p,
    response_format=response_format_dict,
    metadata=assistant.metadata
  )

async def get_all_vector_stores(client) -> List[CoaiVectorStore]:
  all_vector_stores = []
  # Use async iteration to get all vector stores
  async for vector_store in client.vector_stores.list():
    all_vector_stores.append(_convert_to_coai_vector_store(vector_store))
  return all_vector_stores

async def get_all_files(client) -> List[CoaiFile]:
  all_files = []
  # Use async iteration to get all files
  async for file in client.files.list():
    all_files.append(_convert_to_coai_file(file))
  return all_files

async def get_all_files_as_dict(client) -> Dict[str, CoaiFile]:
  """Get all files as a dictionary with file_id as key."""
  all_files_dict = {}
  # Use async iteration to get all files
  async for file in client.files.list():
    coai_file = _convert_to_coai_file(file)
    all_files_dict[coai_file.id] = coai_file
  return all_files_dict

async def get_all_assistants(client) -> List[CoaiAssistant]:
  all_assistants = []
  # Use async iteration to get all assistants
  async for assistant in client.beta.assistants.list():
    all_assistants.append(_convert_to_coai_assistant(assistant))
  return all_assistants

async def get_vector_store_files_with_filenames_as_dict(client, vector_store_id: str) -> Dict[str, CoaiVectorStoreFile]:
  """
  Get all files from a vector store and add attributes from the global files list.
  
  This async function retrieves all files in a vector store and enriches them with
  metadata (filename, bytes, purpose, created_at) from the global files list.
  
  Args:
    client: AsyncAzureOpenAI or AsyncOpenAI client
    vector_store_id: ID of the vector store to retrieve files from
    
  Returns:
    Dictionary with file_id as key and CoaiVectorStoreFile objects as values
  """
  # Get vector store files and global files in parallel for better performance
  async def get_vs_files_dict():
    vs_files_dict = {}
    async for file in client.vector_stores.files.list(vector_store_id=vector_store_id):
      file_id = getattr(file, 'id', None)
      if file_id:
        vs_files_dict[file_id] = file
    return vs_files_dict
  
  vector_store_files_dict, global_files_dict = await asyncio.gather( get_vs_files_dict(), get_all_files_as_dict(client) )
  
  # Enrich vector store files with global file metadata and create dictionary
  files_with_filenames_dict = {}
  for file_id, vs_file in vector_store_files_dict.items():
    # Get global file metadata if available
    global_file = global_files_dict.get(file_id)
    # Convert using helper function and add to dictionary
    files_with_filenames_dict[file_id] = _convert_to_coai_vector_store_file(vs_file, global_file)
  
  return files_with_filenames_dict

async def create_vector_store(client: AsyncAzureOpenAI | AsyncOpenAI, vector_store_name: str, chunk_size: int = 4096, chunk_overlap: int = 2048) -> CoaiVectorStore:
  """Create a new vector store with specified chunking strategy (async).
  
  Args:
    client: Async OpenAI client
    vector_store_name: Name of the vector store to create
    chunk_size: Maximum chunk size in tokens (default: 4096)
    chunk_overlap: Chunk overlap in tokens (default: 2048)
  
  Returns:
    CoaiVectorStore object
  """
  chunking_strategy = {"type": "static", "static": {"max_chunk_size_tokens": chunk_size, "chunk_overlap_tokens": chunk_overlap}}
  vector_store = await client.vector_stores.create(name=vector_store_name, chunking_strategy=chunking_strategy)
  return _convert_to_coai_vector_store(vector_store)

async def try_get_vector_store_by_id(client: AsyncAzureOpenAI | AsyncOpenAI, vector_store_id: str) -> Optional[CoaiVectorStore]:
  """Try to get a vector store by ID (async). Returns None if not found.
  
  Args:
    client: Async OpenAI client
    vector_store_id: ID of the vector store
  
  Returns:
    CoaiVectorStore object or None if not found
  """
  if not vector_store_id: return None
  try:
    vector_store = await client.vector_stores.retrieve(vector_store_id)
    return _convert_to_coai_vector_store(vector_store)
  except Exception as e:
    return None

async def replicate_vector_store_content(client: AsyncAzureOpenAI | AsyncOpenAI, source_vector_store_ids: str | list[str], target_vector_store_ids: str | list[str], remove_target_files_not_in_sources: bool = False) -> tuple[list, list, list]:
  """Replicate files from source to target vector stores (async).
  
  Args:
    client: Async OpenAI client
    source_vector_store_ids: Source vector store ID(s) - string or list of strings
    target_vector_store_ids: Target vector store ID(s) - string or list of strings
    remove_target_files_not_in_sources: If True, remove files from target that don't exist in sources
  
  Returns:
    Tuple of (added_file_ids, removed_file_ids, errors) where:
      - added_file_ids: List of lists of file IDs successfully added to each target store
      - removed_file_ids: List of lists of file IDs removed from each target store
      - errors: List of lists of (file_id, error_message) tuples for failed operations
  """
  # Check if source_vector_store_ids or target_vector_store_ids is string and if yes, create list with single entry
  if isinstance(source_vector_store_ids, str): source_vector_store_ids = [source_vector_store_ids]
  if isinstance(target_vector_store_ids, str): target_vector_store_ids = [target_vector_store_ids]
  
  collected_file_ids_and_source_vector_stores = []; added_file_ids = []; removed_file_ids = []; errors = []
  
  # Collect files from all source vector stores
  for source_vs_id in source_vector_store_ids:
    source_vs = await try_get_vector_store_by_id(client, source_vs_id)
    if not source_vs:
      raise ValueError(f"Source vector store ID='{source_vs_id}' not found")
    source_vs_name = getattr(source_vs, 'name', source_vs_id)
    
    # Get source files
    source_file_ids = []
    async for file in client.vector_stores.files.list(vector_store_id=source_vs_id):
      if getattr(file, 'id', None): source_file_ids.append(file.id)
    
    collected_file_ids_and_source_vector_stores.extend([(file_id, source_vs) for file_id in source_file_ids])
  
  # Process each target vector store
  for i, target_vs_id in enumerate(target_vector_store_ids):
    target_vs = await try_get_vector_store_by_id(client, target_vs_id)
    if not target_vs:
      raise ValueError(f"Target vector store ID='{target_vs_id}' not found")
    target_vs_name = getattr(target_vs, 'name', target_vs_id)
    
    # Get target files
    target_file_ids = []
    async for file in client.vector_stores.files.list(vector_store_id=target_vs_id):
      if getattr(file, 'id', None): target_file_ids.append(file.id)
    
    # Find out which files are not in target
    file_ids_missing_in_target_vs = [(file_id, source_vs) for (file_id, source_vs) in collected_file_ids_and_source_vector_stores if file_id not in target_file_ids]
    file_ids_in_target_but_not_in_collected_files = [file_id for file_id in target_file_ids if file_id not in [f[0] for f in collected_file_ids_and_source_vector_stores]]
    
    added_target_file_ids = []; removed_target_file_ids = []; target_errors = []
    
    # Add files to target
    for j, (file_id, source_vs) in enumerate(file_ids_missing_in_target_vs):
      source_vs_name = getattr(source_vs, 'name', source_vs.id)
      try:
        await client.vector_stores.files.create(vector_store_id=target_vs_id, file_id=file_id)
        added_target_file_ids.append((file_id, source_vs))
      except Exception as e:
        target_errors.append((file_id, f"FAILED: Add file ID='{file_id}' from '{source_vs_name}' to vector store '{target_vs_name}': {str(e)}"))
    
    # Remove files not in source
    if remove_target_files_not_in_sources and len(file_ids_in_target_but_not_in_collected_files) > 0:
      for j, file_id in enumerate(file_ids_in_target_but_not_in_collected_files):
        try:
          await client.vector_stores.files.delete(vector_store_id=target_vs_id, file_id=file_id)
          removed_target_file_ids.append(file_id)
        except Exception as e:
          target_errors.append((file_id, f"FAILED: Remove file ID='{file_id}' from vector store '{target_vs_name}': {str(e)}"))
    
    # Add to return values
    added_file_ids.append(added_target_file_ids)
    removed_file_ids.append(removed_target_file_ids)
    errors.append(target_errors)
  
  return (added_file_ids, removed_file_ids, errors)

async def delete_vector_store_by_id(client: AsyncAzureOpenAI | AsyncOpenAI, vector_store_id: str, delete_files: bool = False, logger: Optional[MiddlewareLogger] = None) -> tuple[bool, str]:
  """Delete a vector store by ID with optional file deletion (async).
  
  Args:
    client: Async OpenAI client
    vector_store_id: ID of the vector store to delete
    delete_files: If True, also delete all files from global storage
    logger: Optional MiddlewareLogger instance for logging output
    
  Returns:
    Tuple of (success: bool, message: str)
  """
  try:
    # Get the vector store first
    vector_store = await try_get_vector_store_by_id(client, vector_store_id)
    if not vector_store:
      return (False, f"Vector store ID='{vector_store_id}' not found")
    
    vs_name = vector_store.name
    if logger: logger.log_function_output(f"Deleting vector store '{vs_name}' (ID={vector_store_id})...")
    
    if delete_files:
      # Get all files in the vector store
      file_ids = []
      async for file in client.vector_stores.files.list(vector_store_id=vector_store_id):
        if getattr(file, 'id', None):
          file_ids.append(file.id)
      
      if logger: logger.log_function_output(f"Deleting {len(file_ids)} files from global storage...")
      
      # Delete each file from global storage
      deleted_count = 0
      failed_count = 0
      for i, file_id in enumerate(file_ids):
        try:
          await client.files.delete(file_id=file_id)
          deleted_count += 1
          if logger: logger.log_function_output(f"  [ {i+1} / {len(file_ids)} ] Deleted file ID={file_id}")
        except Exception as e:
          failed_count += 1
          if logger: logger.log_function_output(f"  [ {i+1} / {len(file_ids)} ] WARNING: Failed to delete file ID={file_id} -> {str(e)}")
      
      if logger: logger.log_function_output(f"  {deleted_count} deleted, {failed_count} failed.")
    
    # Delete the vector store
    await client.vector_stores.delete(vector_store_id)
    
    return (True, f"Vector store '{vs_name}' deleted successfully")
    
  except Exception as e:
    error_msg = f"Failed to delete vector store: {str(e)}"
    if logger: logger.log_function_output(f"ERROR: {error_msg}")
    return (False, error_msg)

async def remove_file_from_vector_store(client: AsyncAzureOpenAI | AsyncOpenAI, vector_store_id: str, file_id: str, logger: Optional[MiddlewareLogger] = None) -> tuple[bool, str]:
  """Remove a file from a vector store (file remains in global storage).
  
  Args:
    client: Async OpenAI client
    vector_store_id: ID of the vector store
    file_id: ID of the file to remove
    logger: Optional MiddlewareLogger instance for logging output
    
  Returns:
    Tuple of (success: bool, message: str)
  """
  try:
    await client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file_id)
    message = f"File {file_id} removed from vector store {vector_store_id}"
    if logger: logger.log_function_output(message)
    return (True, message)
  except Exception as e:
    error_msg = f"Failed to remove file from vector store: {str(e)}"
    if logger: logger.log_function_output(f"ERROR: {error_msg}")
    return (False, error_msg)

async def delete_file_from_vector_store_and_storage(client: AsyncAzureOpenAI | AsyncOpenAI, vector_store_id: str, file_id: str, logger: Optional[MiddlewareLogger] = None) -> tuple[bool, str]:
  """Delete a file from a vector store AND from global storage.
  
  Args:
    client: Async OpenAI client
    vector_store_id: ID of the vector store
    file_id: ID of the file to delete
    logger: Optional MiddlewareLogger instance for logging output
    
  Returns:
    Tuple of (success: bool, message: str)
  """
  try:
    # Remove file from vector store first
    try:
      await client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file_id)
      if logger: logger.log_function_output(f"File {file_id} removed from vector store {vector_store_id}")
    except Exception as e:
      if logger: logger.log_function_output(f"WARNING: Could not remove file from vector store: {str(e)}")
    
    # Delete file from global storage
    await client.files.delete(file_id=file_id)
    message = f"File {file_id} deleted from vector store and global storage"
    if logger: logger.log_function_output(message)
    return (True, message)
  except Exception as e:
    error_msg = f"Failed to delete file: {str(e)}"
    if logger: logger.log_function_output(f"ERROR: {error_msg}")
    return (False, error_msg)

async def delete_file_by_id(client: AsyncAzureOpenAI | AsyncOpenAI, file_id: str, logger: Optional[MiddlewareLogger] = None) -> tuple[bool, str]:
  """Delete a file from global storage by ID.
  
  Args:
    client: Async OpenAI client
    file_id: ID of the file to delete
    logger: Optional MiddlewareLogger instance for logging output
    
  Returns:
    Tuple of (success: bool, message: str)
  """
  try:
    await client.files.delete(file_id=file_id)
    message = f"File {file_id} deleted from global storage"
    if logger: logger.log_function_output(message)
    return (True, message)
  except Exception as e:
    error_msg = f"Failed to delete file: {str(e)}"
    if logger: logger.log_function_output(f"ERROR: {error_msg}")
    return (False, error_msg)

async def delete_assistant_by_id(client: AsyncAzureOpenAI | AsyncOpenAI, assistant_id: str, logger: Optional[MiddlewareLogger] = None) -> tuple[bool, str]:
  """Delete an assistant by ID.
  
  Args:
    client: Async OpenAI client
    assistant_id: ID of the assistant to delete
    logger: Optional MiddlewareLogger instance for logging output
    
  Returns:
    Tuple of (success: bool, message: str)
  """
  try:
    await client.beta.assistants.delete(assistant_id=assistant_id)
    message = f"Assistant {assistant_id} deleted successfully"
    if logger: logger.log_function_output(message)
    return (True, message)
  except Exception as e:
    error_msg = f"Failed to delete assistant: {str(e)}"
    if logger: logger.log_function_output(f"ERROR: {error_msg}")
    return (False, error_msg)
  
# ----------------------------------------------------- END: Vector stores ----------------------------------------------------
