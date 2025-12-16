# Test router for streaming endpoints
import asyncio
import json
import random
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from routers_v1.common_ui_functions import generate_documentation_page
from routers_v1.common_job_functions import create_streaming_state_file, delete_streaming_state_file, generate_streaming_operation_id, get_streaming_current_state, get_streaming_state_folder, list_streaming_operations, rename_streaming_state_file, streaming_state_file_exists
from logging_v1 import log_function_footer, log_function_header

router = APIRouter()

# Configuration will be injected from app.py
config = None
router_prefix = ""

# Set the configuration for test router. app_config: Config dataclass with openai_client, persistent_storage_path, etc.
def set_config(app_config, prefix: str = ""):
  global config, router_prefix
  config = app_config
  router_prefix = prefix


@router.get('/testrouter/streaming01')
async def streaming01(request: Request):
  """
  Test endpoint for streaming responses simulating long-running file processing.
  
  Simulates processing files with 200ms delay each. Streams plain text logs
  followed by a JSON summary. Supports cancel/pause/resume via state files.
  
  Parameters:
  - format: 'stream' to start streaming response
  - files: Number of simulated files (default: 20)
  
  Examples:
  /testrouter/streaming01?format=stream
  /testrouter/streaming01?format=stream&files=5
  
  Control:
  - GET /testrouter/control?id=...&action=pause
  - GET /testrouter/control?id=...&action=resume
  - GET /testrouter/control?id=...&action=cancel
  - GET /testrouter/operations - list active operations
  
  Output format:
  <start_json>
  {"id": "testrouter-streaming01_2025-11-25_17-42-00_p16192_r12", "total": 20}
  </start_json>
  <log>
  [ 1 / 20 ] Processing file 'document_001.pdf'...
    OK.
  ...
  </log>
  <end_json>
  {"result": "success", "total": 20, "processed": 18, "failed": 2, ...}
  </end_json>
  """
  function_name = 'streaming01()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(log_data)
    return HTMLResponse(generate_documentation_page('/testrouter/streaming01', streaming01.__doc__))

  response_format = request_params.get('format', 'stream')
  file_count = int(request_params.get('files', '20'))

  if response_format == 'stream':
    # Get state folder and generate operation ID
    state_folder = get_streaming_state_folder(config.LOCAL_PERSISTENT_STORAGE_PATH if config else None)
    operation_id = generate_streaming_operation_id("testrouter-streaming01", log_data)
    
    # Create initial state file
    if state_folder:
      create_streaming_state_file(state_folder, operation_id, "running")

    async def generate_stream():
      # Simulated file list
      simulated_files = [f"document_{i:03d}.pdf" for i in range(1, file_count + 1)]
      processed_files = []
      failed_files = []
      final_state = "completed"
      was_cancelled = False

      # HEADER_JSON section
      yield "<start_json>\n"
      header_data = {"id": operation_id, "total": len(simulated_files)}
      yield json.dumps(header_data) + "\n"
      yield "</start_json>\n"

      # LOG section
      yield "<log>\n"

      for index, filename in enumerate(simulated_files, start=1):
        # Check for cancel request
        if state_folder and streaming_state_file_exists(state_folder, operation_id, "cancel_requested"):
          yield f"  Cancel requested, stopping...\n"
          delete_streaming_state_file(state_folder, operation_id, "cancel_requested")
          delete_streaming_state_file(state_folder, operation_id, "running")
          delete_streaming_state_file(state_folder, operation_id, "paused")
          final_state = "cancelled"
          was_cancelled = True
          break

        # Check for pause request
        if state_folder and streaming_state_file_exists(state_folder, operation_id, "pause_requested"):
          yield f"  Pause requested, pausing...\n"
          delete_streaming_state_file(state_folder, operation_id, "pause_requested")
          rename_streaming_state_file(state_folder, operation_id, "running", "paused")

        # Wait while paused
        while state_folder and streaming_state_file_exists(state_folder, operation_id, "paused"):
          if streaming_state_file_exists(state_folder, operation_id, "resume_requested"):
            yield f"  Resume requested, resuming...\n"
            delete_streaming_state_file(state_folder, operation_id, "resume_requested")
            rename_streaming_state_file(state_folder, operation_id, "paused", "running")
            break
          if streaming_state_file_exists(state_folder, operation_id, "cancel_requested"):
            yield f"  Cancel requested while paused, stopping...\n"
            delete_streaming_state_file(state_folder, operation_id, "cancel_requested")
            delete_streaming_state_file(state_folder, operation_id, "paused")
            final_state = "cancelled"
            was_cancelled = True
            break
          await asyncio.sleep(0.1)

        if was_cancelled:
          break

        yield f"[ {index} / {len(simulated_files)} ] Processing file '{filename}'...\n"

        # Simulate processing time (200ms)
        await asyncio.sleep(0.2)

        # Simulate occasional failures (10% chance)
        if random.random() < 0.1:
          yield f"  FAIL: Simulated error for '{filename}'\n"
          failed_files.append({"filename": filename, "error": "Simulated processing error"})
        else:
          yield f"  OK.\n"
          processed_files.append({"filename": filename, "size_bytes": random.randint(10000, 500000)})

      # Clean up: delete state file on completion (no garbage left)
      if state_folder and not was_cancelled:
        delete_streaming_state_file(state_folder, operation_id, "running")

      yield "</log>\n"

      # FOOTER_JSON section
      yield "<end_json>\n"

      if was_cancelled: result = "cancelled"
      elif len(failed_files) == 0: result = "success"
      else: result = "partial"

      result_data = {
        "result": result,
        "state": final_state,
        "total": len(simulated_files),
        "processed": len(processed_files),
        "failed": len(failed_files),
        "processed_files": processed_files,
        "failed_files": failed_files
      }
      yield json.dumps(result_data, indent=2) + "\n"

      yield "</end_json>\n"

      # Log footer inside generator to capture actual streaming duration
      await log_function_footer(log_data)

    return StreamingResponse(generate_stream(), media_type="text/event-stream; charset=utf-8")


@router.get('/testrouter/control')
async def control_operation(request: Request):
  """
  Control a running streaming operation (pause/resume/cancel).
  
  Parameters:
  - id: The operation ID (from HEADER_JSON in stream output)
  - action: 'pause', 'resume', or 'cancel'
  
  Examples:
  GET /testrouter/control?id=testrouter-streaming01_2025-11-25_17-42-00_p16192_r12&action=pause
  GET /testrouter/control?id=testrouter-streaming01_2025-11-25_17-42-00_p16192_r12&action=resume
  GET /testrouter/control?id=testrouter-streaming01_2025-11-25_17-42-00_p16192_r12&action=cancel
  """
  function_name = 'control_operation()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  if len(request_params) == 0:
    await log_function_footer(log_data)
    return HTMLResponse(generate_documentation_page('/testrouter/control', control_operation.__doc__))

  operation_id = request_params.get('id')
  action = request_params.get('action')

  if not operation_id or not action:
    await log_function_footer(log_data)
    return JSONResponse({"error": "Missing 'id' or 'action' parameter"}, status_code=400)

  if action not in ["pause", "resume", "cancel"]:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Invalid action '{action}'. Must be 'pause', 'resume', or 'cancel'"}, status_code=400)

  state_folder = get_streaming_state_folder(config.LOCAL_PERSISTENT_STORAGE_PATH if config else None)
  if not state_folder:
    await log_function_footer(log_data)
    return JSONResponse({"error": "State folder not configured"}, status_code=500)

  current_state = get_streaming_current_state(state_folder, operation_id)
  if not current_state:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Operation '{operation_id}' not found or already finished"}, status_code=404)

  # Create the request file
  create_streaming_state_file(state_folder, operation_id, f"{action}_requested")

  await log_function_footer(log_data)
  return JSONResponse({"success": True, "id": operation_id, "action": action, "message": f"{action.capitalize()} requested for operation '{operation_id}'"})


@router.get('/testrouter/operations')
async def list_active_operations(request: Request):
  """
  List all active streaming operations (running or paused).
  
  Parameters:
  - endpoint: Optional filter by endpoint name (e.g., 'testrouter-streaming01')
  
  Examples:
  GET /testrouter/operations
  GET /testrouter/operations?endpoint=testrouter-streaming01
  """
  function_name = 'list_active_operations()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  state_folder = get_streaming_state_folder(config.LOCAL_PERSISTENT_STORAGE_PATH if config else None)
  endpoint_filter = request_params.get('endpoint')
  operations = list_streaming_operations(state_folder, endpoint_filter)

  await log_function_footer(log_data)
  return JSONResponse({"operations": operations, "count": len(operations)})
