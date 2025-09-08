# Common Open AI functions (COAI)
# Copyright 2025, Karsten Held (MIT License)

from azure.identity.aio import DefaultAzureCredential, ClientSecretCredential, get_bearer_token_provider
from azure.identity import ClientSecretCredential as SyncClientSecretCredential
from azure.identity import DefaultAzureCredential as SyncDefaultAzureCredential
from azure.identity import get_bearer_token_provider as sync_get_bearer_token_provider
from azure.core.credentials import TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
import openai
import httpx
from dataclasses import dataclass
from typing import List, Optional, Union, Iterable, Literal, Dict
from openai.types.responses import (ResponseInputParam,ResponseTextConfigParam,ToolParam)
from openai.types.responses.response_includable import ResponseIncludable
from openai.types.responses.response_prompt_param import ResponsePromptParam
from openai.types.shared_params.responses_model import ResponsesModel
from openai.types.shared_params.metadata import Metadata
from openai.types.shared_params.reasoning import Reasoning
from openai.types.responses import response_create_params
from openai._types import NOT_GIVEN, NotGiven
from openai._types import Headers, Query, Body
import time
from utils import log_function_output
import os

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

def create_openai_client(api_key):
  if not api_key:
    raise ValueError("OPENAI_API_KEY is required when OPENAI_SERVICE_TYPE is set to 'openai'")
  return openai.OpenAI(api_key=api_key)

# Create an Azure OpenAI client using API key authentication
def create_azure_openai_client_with_api_key(endpoint, api_version, api_key):
  if not endpoint or not api_key:
    raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are required for Azure OpenAI key authentication")
  return openai.AzureOpenAI(api_version=api_version, azure_endpoint=endpoint, api_key=api_key)

# Create an async Azure OpenAI client using API key authentication
def create_async_azure_openai_client_with_api_key(endpoint, api_version, api_key):
  if not endpoint or not api_key:
    raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are required for Azure OpenAI key authentication")
  return openai.AsyncAzureOpenAI(api_version=api_version, azure_endpoint=endpoint, api_key=api_key)

# Create an Azure OpenAI client with any TokenCredential
# ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
# SyncDefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
def create_azure_openai_client_with_credential(endpoint, api_version, credential: TokenCredential):
  if not endpoint:
    raise ValueError("AZURE_OPENAI_ENDPOINT is required for Azure OpenAI credential authentication")
  token_provider = sync_get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
  return openai.AzureOpenAI(api_version=api_version, azure_endpoint=endpoint, azure_ad_token_provider=token_provider)

# Create an async Azure OpenAI client with any AsyncTokenCredential
# ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)
# DefaultAzureCredential(managed_identity_client_id=managed_identity_client_id)
def create_async_azure_openai_client_with_credential(endpoint, api_version, credential: AsyncTokenCredential):
  if not endpoint:
    raise ValueError("AZURE_OPENAI_ENDPOINT is required for Azure OpenAI credential authentication")
  token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
  return openai.AsyncAzureOpenAI(api_version=api_version, azure_endpoint=endpoint, azure_ad_token_provider=token_provider, max_retries=5)

# Retries the given function on rate limit errors
def retry_on_openai_rate_limit_errors_for_sync_client(fn, function_name="retry_on_openai_errors", request_number=0, indentation=0, retries=5, backoff_seconds=10):
  for attempt in range(retries):
    try:
      return fn()
    except Exception as e:
      # Only retry on rate limit errors
      if not (hasattr(e, 'type') and e.type == 'rate_limit_error'):
        raise e
      if attempt == retries - 1:  # Last attempt
        raise e
      log_function_output(function_name, request_number, f"{' '*indentation}Rate limit reached, retrying in {backoff_seconds} seconds... (attempt {attempt + 2} of {retries})")
      time.sleep(backoff_seconds)

# Uses the file_search tool of the Responses API to get search results from a vector store
# Why? As of 2025-09-08, Azure Open AI Services does not support the Search API. This is a temporary workaround to get similar results.
# -> Client error '404 Resource Not Found' for url 'https://<ai-resource>.cognitiveservices.azure.com/openai/vector_stores/<VECTOR-STORE-ID>/search?api-version=2025-04-01-preview'
# https://platform.openai.com/docs/guides/tools-file-search
# https://github.com/openai/openai-python/blob/main/src/openai/resources/responses/responses.py
async def get_search_results_using_responses(openai_client, search_params: CoaiSearchParams, vector_store_id: str, model: str, instructions: str) -> tuple[List[CoaiSearchResults], any]:
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
      content = [CoaiSearchContent(text=result.text, type="text")]
      item = CoaiSearchResults(attributes=result.attributes, content=content, file_id=result.file_id, filename=result.filename, score=result.score)
      search_results.append(item)
  
  return search_results, search_response

# Tries to get the vector store by id and returns None if it fails
async def try_get_vector_store_by_id(client, vsid):
  try:
    return await client.vector_stores.retrieve(vsid)
  except Exception as e:
    return None

# Utility function to remove temperature parameter for reasoning models that don't support it
# When reasoning model is used, it will add the reasoning effort if specified
def remove_temperature_from_request_params_for_reasoning_models(request_params, model_name, reasoning_effort=None):
  if (model_name.startswith('o') or model_name.startswith('gpt-5')) and 'temperature' in request_params:
    del request_params['temperature']
  
  # Add reasoning parameter for reasoning models if reasoning_effort is specified
  if reasoning_effort and reasoning_effort in ["minimal", "low", "medium", "high"]:
    if model_name.startswith('o') or model_name.startswith('gpt-5'):
      # For 'o' models, 'minimal' is invalid and will be mapped to 'low'
      if model_name.startswith('o') and reasoning_effort == "minimal": request_params["reasoning"] = {"effort": "low"}
      else: request_params["reasoning"] = {"effort": reasoning_effort}
