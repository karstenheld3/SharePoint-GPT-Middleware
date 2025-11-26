# V2 Streaming Test Router - implements file-based streaming with monitor capability
import asyncio, datetime, json, random
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from common_job_functions import StreamingJob, generate_streaming_job_id, create_streaming_job_file, create_streaming_job_control_file, find_streaming_job_file, write_streaming_job_log, rename_streaming_job_file, delete_streaming_job_file, streaming_job_file_exists, get_streaming_job_current_state, find_streaming_job_by_id, list_streaming_jobs
from common_ui_functions import generate_documentation_page, generate_ui_table_page, generate_table_rows_with_actions, generate_error_div
from utils import log_function_footer, log_function_header

router = APIRouter()

# Configuration will be injected from app.py
config = None

ROUTER_NAME = "testrouter2"

# Set the configuration for test router. app_config: Config dataclass with openai_client, persistent_storage_path, etc.
def set_config(app_config):
  global config
  config = app_config


# Helper: Generate action buttons based on job state
def get_job_action_buttons(job: dict) -> list:
  sj_id = job['sj_id']
  buttons = [
    {'text': 'Monitor', 'onclick': f"window.open('/testrouter2/monitor?sj_id={sj_id}', '_blank')",
     'button_class': 'btn-small'}
  ]
  
  if job['state'] == 'running':
    buttons.extend([
      {'text': 'Pause', 'hx_method': 'get', 'hx_endpoint': f'/testrouter2/control?sj_id={sj_id}&action=pause&format=ui',
       'hx_target': f'#job-{sj_id}', 'hx_swap': 'outerHTML', 'button_class': 'btn-small'},
      {'text': 'Cancel', 'hx_method': 'get', 'hx_endpoint': f'/testrouter2/control?sj_id={sj_id}&action=cancel&format=ui',
       'hx_target': f'#job-{sj_id}', 'hx_swap': 'outerHTML', 'button_class': 'btn-small btn-delete',
       'confirm_message': f'Cancel job {sj_id}?'}
    ])
  elif job['state'] == 'paused':
    buttons.extend([
      {'text': 'Resume', 'hx_method': 'get', 'hx_endpoint': f'/testrouter2/control?sj_id={sj_id}&action=resume&format=ui',
       'hx_target': f'#job-{sj_id}', 'hx_swap': 'outerHTML', 'button_class': 'btn-small'},
      {'text': 'Cancel', 'hx_method': 'get', 'hx_endpoint': f'/testrouter2/control?sj_id={sj_id}&action=cancel&format=ui',
       'hx_target': f'#job-{sj_id}', 'hx_swap': 'outerHTML', 'button_class': 'btn-small btn-delete',
       'confirm_message': f'Cancel job {sj_id}?'}
    ])
  
  return buttons


# ---------------------------------------------------- START: Streaming Endpoint --------------------------------------------------

@router.get('/streaming01')
async def streaming01(request: Request):
  """
  V2 Streaming Test Endpoint - simulates file processing with log persistence.
  
  Writes to log file AND streams to client. Supports pause/resume/cancel.
  Multiple clients can monitor the same job via /streaming_jobs/monitor.
  
  Parameters:
  - format: 'stream' to start streaming response (default shows docs)
  - files: Number of files to simulate (default: 20)
  
  Examples:
  /testrouter2/streaming01?format=stream
  /testrouter2/streaming01?format=stream&files=10
  
  Control:
  - GET /testrouter2/control?sj_id=42&action=pause
  - GET /testrouter2/control?sj_id=42&action=resume
  - GET /testrouter2/control?sj_id=42&action=cancel
  
  Monitor:
  - GET /testrouter2/monitor?sj_id=42
  
  Output format:
  <start_json>
  {"sj_id": 42, "monitor_url": "/testrouter2/monitor?sj_id=42", "total": 20}
  </start_json>
  <log>
  [ 1 / 20 ] Processing 'document_001.pdf'...
    OK.
  ...
  </log>
  <end_json>
  {"result": "success", "state": "completed", "sj_id": 42, ...}
  </end_json>
  """
  function_name = 'streaming01()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  # Display documentation if no params are provided
  if len(request_params) == 0:
    await log_function_footer(log_data)
    return HTMLResponse(generate_documentation_page('/testrouter2/streaming01', streaming01.__doc__))

  response_format = request_params.get('format', 'stream')
  file_count = int(request_params.get('files', '20'))

  if response_format != 'stream':
    await log_function_footer(log_data)
    return JSONResponse({"message": "Use format=stream for streaming response", "files": file_count})

  # Check config
  if not config or not config.LOCAL_PERSISTENT_STORAGE_PATH:
    await log_function_footer(log_data)
    return JSONResponse({"error": "LOCAL_PERSISTENT_STORAGE_PATH not configured"}, status_code=500)

  storage_path = config.LOCAL_PERSISTENT_STORAGE_PATH
  endpoint_name = "streaming01"

  # Generate unique job ID with retry on collision
  max_retries = 3
  sj_id = None
  job_timestamp = None

  for attempt in range(max_retries):
    sj_id = generate_streaming_job_id(storage_path)
    success, job_timestamp = create_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "running")
    if success: break
    sj_id = None
    job_timestamp = None

  if sj_id is None:
    await log_function_footer(log_data)
    return JSONResponse({"error": "Failed to create streaming job after retries"}, status_code=500)

  source_url = f"{request.url.path}?{request.query_params}" if request.query_params else str(request.url.path)

  async def generate_stream():
    simulated_files = [f"document_{i:03d}.pdf" for i in range(1, file_count + 1)]
    processed_files = []
    failed_files = []

    # Initialize StreamingJob
    job = StreamingJob(
      sj_id=sj_id,
      source_url=source_url,
      monitor_url=f"/testrouter2/monitor?sj_id={sj_id}",
      router=ROUTER_NAME,
      endpoint=endpoint_name,
      state="RUNNING",
      total=file_count,
      current=0,
      started=datetime.datetime.now(),
      finished=None,
      result=None,
      result_data=None
    )

    # ----- HEADER SECTION -----
    header_text = f"<start_json>\n{json.dumps(asdict(job), indent=2, default=str)}\n</start_json>\n"
    write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, header_text)
    yield header_text

    # ----- LOG SECTION START -----
    log_start = "<log>\n"
    write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, log_start)
    yield log_start

    # ----- PROCESS ITEMS -----
    for index, filename in enumerate(simulated_files, start=1):

      # Check for cancel request
      if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "cancel_requested"):
        cancel_msg = "  Cancel requested, stopping...\n"
        write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, cancel_msg)
        yield cancel_msg
        delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "cancel_requested")
        job.state = "CANCELED"
        job.result = "CANCELED"
        break

      # Check for pause request
      if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "pause_requested"):
        pause_msg = "  Pause requested, pausing...\n"
        write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, pause_msg)
        yield pause_msg
        delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "pause_requested")
        rename_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "running", "paused")

      # Wait while paused
      while streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "paused"):
        # Check for cancel while paused
        if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "cancel_requested"):
          cancel_msg = "  Cancel requested while paused, stopping...\n"
          write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, cancel_msg)
          yield cancel_msg
          delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "cancel_requested")
          delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "paused")
          job.state = "CANCELED"
          job.result = "CANCELED"
          break

        # Check for resume request
        if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, "resume_requested"):
          resume_msg = "  Resume requested, resuming...\n"
          write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, resume_msg)
          yield resume_msg
          delete_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "resume_requested")
          rename_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, "paused", "running")
          break

        await asyncio.sleep(0.1)

      # Check if we were canceled while paused
      if job.state == "CANCELED": break

      # Process item
      progress_msg = f"[ {index} / {file_count} ] Processing '{filename}'...\n"
      write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, progress_msg)
      yield progress_msg

      await asyncio.sleep(0.2)  # Simulate work

      # Simulate random failures (10% chance)
      if random.random() < 0.1:
        fail_msg = f"  FAIL: Simulated error for '{filename}'\n"
        write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, fail_msg)
        yield fail_msg
        failed_files.append({"filename": filename, "error": "Simulated error"})
      else:
        ok_msg = "  OK.\n"
        write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, ok_msg)
        yield ok_msg
        processed_files.append({"filename": filename, "size_bytes": random.randint(10000, 500000)})

    # ----- LOG SECTION END -----
    log_end = "</log>\n"
    write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, log_end)
    yield log_end

    # ----- FOOTER SECTION -----
    job.current = len(processed_files) + len(failed_files)
    job.finished = datetime.datetime.now()
    
    if job.result != "CANCELED":
      job.state = "COMPLETED"
      job.result = "PARTIAL" if failed_files else "OK"
    
    job.result_data = {
      "processed": len(processed_files),
      "failed": len(failed_files),
      "processed_files": processed_files,
      "failed_files": failed_files
    }

    footer_text = f"<end_json>\n{json.dumps(asdict(job), indent=2, default=str)}\n</end_json>\n"
    write_streaming_job_log(storage_path, ROUTER_NAME, endpoint_name, sj_id, footer_text)
    yield footer_text

    # ----- FINALIZE STATE -----
    for current_state in ["running", "paused"]:
      if streaming_job_file_exists(storage_path, ROUTER_NAME, endpoint_name, sj_id, current_state):
        rename_streaming_job_file(storage_path, ROUTER_NAME, endpoint_name, sj_id, current_state, job.state)
        break

    await log_function_footer(log_data)

  return StreamingResponse(generate_stream(), media_type="text/event-stream; charset=utf-8")

# ---------------------------------------------------- END: Streaming Endpoint ----------------------------------------------------


# ----------------------------------------------------- START: Monitor Endpoint ---------------------------------------------------

@router.get('/monitor')
async def monitor_streaming_job(request: Request):
  """
  Monitor a streaming job by tailing its log file.
  
  Can attach to running, completed, or canceled jobs.
  Multiple monitors can attach to the same job simultaneously.
  
  Parameters:
  - sj_id: Streaming job ID to monitor (required)
  
  Examples:
  /testrouter2/monitor?sj_id=42
  """
  function_name = 'monitor_streaming_job()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  if len(request_params) == 0:
    await log_function_footer(log_data)
    return HTMLResponse(generate_documentation_page('/testrouter2/monitor', monitor_streaming_job.__doc__))

  sj_id_str = request_params.get('sj_id')
  if not sj_id_str:
    await log_function_footer(log_data)
    return JSONResponse({"error": "Missing 'sj_id' parameter"}, status_code=400)

  sj_id = int(sj_id_str)

  if not config or not config.LOCAL_PERSISTENT_STORAGE_PATH:
    await log_function_footer(log_data)
    return JSONResponse({"error": "LOCAL_PERSISTENT_STORAGE_PATH not configured"}, status_code=500)

  storage_path = config.LOCAL_PERSISTENT_STORAGE_PATH

  # Find the job
  job_info = find_streaming_job_by_id(storage_path, sj_id)
  if not job_info:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Job {sj_id} not found"}, status_code=404)

  router_name = job_info["router_name"]
  endpoint_name = job_info["endpoint_name"]
  file_path = job_info["file_path"]

  async def tail_log_file():
    with open(file_path, 'r', encoding='utf-8') as f:
      while True:
        chunk = f.read(4096)
        if chunk:
          yield chunk
        else:
          # No more data - check if job is still active
          current_state = get_streaming_job_current_state(storage_path, router_name, endpoint_name, sj_id)
          if current_state in ["running", "paused"]:
            await asyncio.sleep(0.1)
            # Re-check file path in case it was renamed
            new_job_info = find_streaming_job_by_id(storage_path, sj_id)
            if new_job_info and new_job_info["file_path"] != file_path:
              break  # File was renamed, reopen would be needed
          else:
            # Job completed/canceled - do final read to catch any remaining content
            final_chunk = f.read()
            if final_chunk:
              yield final_chunk
            break

  await log_function_footer(log_data)
  return StreamingResponse(tail_log_file(), media_type="text/event-stream; charset=utf-8")

# ----------------------------------------------------- END: Monitor Endpoint -----------------------------------------------------


# ---------------------------------------------------- START: Control Endpoint ----------------------------------------------------

@router.get('/control')
async def control_streaming_job(request: Request):
  """
  Control a streaming job (pause/resume/cancel).
  
  Parameters:
  - sj_id: Streaming job ID (required)
  - action: One of 'pause', 'resume', 'cancel' (required)
  
  Examples:
  /testrouter2/control?sj_id=42&action=pause
  /testrouter2/control?sj_id=42&action=resume
  /testrouter2/control?sj_id=42&action=cancel
  """
  function_name = 'control_streaming_job()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  if len(request_params) == 0:
    await log_function_footer(log_data)
    return HTMLResponse(generate_documentation_page('/testrouter2/control', control_streaming_job.__doc__))

  sj_id_str = request_params.get('sj_id')
  action = request_params.get('action')

  if not sj_id_str or not action:
    await log_function_footer(log_data)
    return JSONResponse({"error": "Missing 'sj_id' or 'action' parameter"}, status_code=400)

  sj_id = int(sj_id_str)
  valid_actions = ["pause", "resume", "cancel"]
  if action not in valid_actions:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Invalid action '{action}'. Must be one of: {valid_actions}"}, status_code=400)

  if not config or not config.LOCAL_PERSISTENT_STORAGE_PATH:
    await log_function_footer(log_data)
    return JSONResponse({"error": "LOCAL_PERSISTENT_STORAGE_PATH not configured"}, status_code=500)

  storage_path = config.LOCAL_PERSISTENT_STORAGE_PATH

  # Find the job
  job_info = find_streaming_job_by_id(storage_path, sj_id)
  if not job_info:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Job {sj_id} not found"}, status_code=404)

  router_name = job_info["router_name"]
  endpoint_name = job_info["endpoint_name"]
  current_state = job_info["state"]
  job_timestamp = job_info["timestamp"]

  # Validate state for action
  if current_state not in ["running", "paused"]:
    await log_function_footer(log_data)
    return JSONResponse({"error": f"Cannot {action} job {sj_id} - job is {current_state}"}, status_code=400)

  # Create control request file
  control_state = f"{action}_requested"
  success = create_streaming_job_control_file(storage_path, router_name, endpoint_name, sj_id, job_timestamp, control_state)

  await log_function_footer(log_data)

  response_format = request_params.get('format', 'json')

  if response_format == 'ui':
    # Re-fetch job to get updated state
    updated_job = find_streaming_job_by_id(storage_path, sj_id)
    if updated_job:
      job_data = {
        'sj_id': sj_id,
        'router': updated_job['router_name'],
        'endpoint': updated_job['endpoint_name'],
        'state': updated_job['state'],
        'created': updated_job['timestamp']
      }
      columns = [
        {'field': 'sj_id', 'header': 'SJ_ID'},
        {'field': 'router', 'header': 'Router'},
        {'field': 'endpoint', 'header': 'Endpoint'},
        {'field': 'state', 'header': 'State'},
        {'field': 'created', 'header': 'Created'},
        {'field': 'actions', 'header': 'Actions', 'buttons': get_job_action_buttons}
      ]
      row_html = generate_table_rows_with_actions([job_data], columns, 'sj_id', 'job')
      return HTMLResponse(row_html)
    return HTMLResponse(generate_error_div(f"Job {sj_id} not found after action"))

  if success:
    return JSONResponse({"success": True, "sj_id": sj_id, "action": action, "message": f"{action.capitalize()} requested for job {sj_id}"})
  else:
    return JSONResponse({"success": False, "sj_id": sj_id, "action": action, "message": f"{action.capitalize()} already requested for job {sj_id}"})

# ---------------------------------------------------- END: Control Endpoint ------------------------------------------------------


# --------------------------------------------------- START: List Jobs Endpoint ---------------------------------------------------

@router.get('/jobs')
async def list_jobs(request: Request):
  """
  List all streaming jobs with optional filters.
  
  Parameters:
  - format: Response format ('json', 'html') - default: 'json'
  - router: Filter by router name
  - endpoint: Filter by endpoint name
  - state: Filter by state ('running', 'paused', 'completed', 'canceled')
  
  Examples:
  /testrouter2/jobs
  /testrouter2/jobs?format=html
  /testrouter2/jobs?state=running
  /testrouter2/jobs?router=testrouter2&state=completed
  """
  function_name = 'list_jobs()'
  log_data = log_function_header(function_name)
  request_params = dict(request.query_params)

  response_format = request_params.get('format', 'json')
  router_filter = request_params.get('router')
  endpoint_filter = request_params.get('endpoint')
  state_filter = request_params.get('state')

  if not config or not config.LOCAL_PERSISTENT_STORAGE_PATH:
    await log_function_footer(log_data)
    return JSONResponse({"error": "LOCAL_PERSISTENT_STORAGE_PATH not configured"}, status_code=500)

  storage_path = config.LOCAL_PERSISTENT_STORAGE_PATH
  jobs = list_streaming_jobs(storage_path, router_filter=router_filter, endpoint_filter=endpoint_filter, state_filter=state_filter)

  await log_function_footer(log_data)

  if response_format == "json":
    return JSONResponse({"jobs": jobs, "count": len(jobs)})

  elif response_format == "ui":
    columns = [
      {'field': 'sj_id', 'header': 'SJ_ID'},
      {'field': 'router', 'header': 'Router'},
      {'field': 'endpoint', 'header': 'Endpoint'},
      {'field': 'state', 'header': 'State'},
      {'field': 'created', 'header': 'Created'},
      {'field': 'actions', 'header': 'Actions', 'buttons': get_job_action_buttons}
    ]
    return HTMLResponse(generate_ui_table_page(
      title="Streaming Jobs",
      count=len(jobs),
      data=jobs,
      columns=columns,
      row_id_field='sj_id',
      row_id_prefix='job',
      back_link='/'
    ))

  elif response_format == "html":
    html = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Streaming Jobs</title><link rel='stylesheet' href='/static/css/styles.css'></head><body>"
    html += f"<h1>Streaming Jobs ({len(jobs)})</h1>"
    html += "<table border='1'><tr><th>SJ_ID</th><th>Router</th><th>Endpoint</th><th>State</th><th>Created</th><th>Actions</th></tr>"

    for job in jobs:
      html += f"<tr>"
      html += f"<td>{job['sj_id']}</td>"
      html += f"<td>{job['router']}</td>"
      html += f"<td>{job['endpoint']}</td>"
      html += f"<td>{job['state']}</td>"
      html += f"<td>{job['created']}</td>"
      html += f"<td>"
      html += f"<a href='/testrouter2/monitor?sj_id={job['sj_id']}'>Monitor</a>"
      if job['state'] == 'running':
        html += f" | <a href='/testrouter2/control?sj_id={job['sj_id']}&action=pause'>Pause</a>"
        html += f" | <a href='/testrouter2/control?sj_id={job['sj_id']}&action=cancel'>Cancel</a>"
      elif job['state'] == 'paused':
        html += f" | <a href='/testrouter2/control?sj_id={job['sj_id']}&action=resume'>Resume</a>"
        html += f" | <a href='/testrouter2/control?sj_id={job['sj_id']}&action=cancel'>Cancel</a>"
      html += f"</td>"
      html += f"</tr>"

    html += "</table>"
    html += "<p><a href='/'>← Back to Main Page</a></p>"
    html += "</body></html>"
    return HTMLResponse(html)

  else:
    return JSONResponse({"jobs": jobs, "count": len(jobs)})

# --------------------------------------------------- END: List Jobs Endpoint -----------------------------------------------------
