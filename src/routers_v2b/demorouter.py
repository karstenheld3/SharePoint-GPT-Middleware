import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from routers_v2b.router_job_functions import ControlAction, StreamingJobWriter
from utils import log_function_footer, log_function_header, log_function_output

router = APIRouter()
config = None
router_prefix = None


def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix


@router.get("/demorouter")
async def demorouter_root(request: Request):
  """Router root for Demo V2B router."""
  return HTMLResponse(f"""
<!doctype html><html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Demo Router V2B</title>
  <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
  <h1>Demo Router V2B</h1>
  <p>Demo router for testing streaming job infrastructure with V2B prefix.</p>

  <h4>Available Endpoints</h4>
  <ul>
    <li><a href="{router_prefix}/demorouter/process_files">{router_prefix}/demorouter/process_files</a> - Process files (<a href="{router_prefix}/demorouter/process_files?format=stream">Stream</a> | <a href="{router_prefix}/demorouter/process_files?format=stream&files=5">Stream 5 files</a>)</li>
  </ul>

  <p><a href="/">← Back to Main Page</a></p>
</body>
</html>
""")


@router.get("/demorouter/process_files")
async def process_files(request: Request):
  """
  Demo streaming endpoint - simulates file processing with streaming output.

  Parameters:
  - format: Must be 'stream' for this endpoint
  - files: Number of files to simulate (default: 20)

  Examples:
  {router_prefix}/demorouter/process_files?format=stream
  {router_prefix}/demorouter/process_files?format=stream&files=10
  """
  function_name = "process_files()"
  request_params = dict(request.query_params)
  endpoint_documentation = process_files.__doc__.replace("{router_prefix}", router_prefix or "")
  documentation_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>/demorouter/process_files - Documentation</title><link rel='stylesheet' href='/static/css/styles.css'></head><body><pre style='white-space: pre-wrap'>{endpoint_documentation}</pre></body></html>"

  if len(request_params) == 0: return HTMLResponse(documentation_html)

  response_format = request_params.get("format", None)
  file_count = int(request_params.get("files", "20"))

  if response_format != "stream": return JSONResponse({"ok": False, "error": "Use format=stream", "data": {}})

  if not config or not getattr(config, "LOCAL_PERSISTENT_STORAGE_PATH", None):
    return JSONResponse({"ok": False, "error": "LOCAL_PERSISTENT_STORAGE_PATH not configured", "data": {}}, status_code=500)

  source_url = f"{router_prefix}/demorouter/process_files?format=stream&files={file_count}"

  async def stream_generator():
    log_data = log_function_header(function_name)

    writer = StreamingJobWriter(
      persistent_storage_path=config.LOCAL_PERSISTENT_STORAGE_PATH,
      router_name="demorouter",
      action="process_files",
      object_id=None,
      source_url=source_url,
      router_prefix=router_prefix,
      buffer_size=CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE
    )

    log_function_output(log_data, f"Created job '{writer.job_id}' for {file_count} files")

    try:
      yield writer.emit_start()
      simulated_files = [f"document_{i:03d}.pdf" for i in range(1, file_count + 1)]
      total = len(simulated_files)

      for i, filename in enumerate(simulated_files, 1):
        control_logs, control = await writer.check_control()
        for log in control_logs: yield log
        if control == ControlAction.CANCEL:
          yield writer.emit_end(ok=False, error="Cancelled by user", data={"processed": i-1, "total": total})
          return

        yield writer.emit_log_with_standard_logging(log_data, f"[ {i} / {total} ] Processing '{filename}'...")
        await asyncio.sleep(0.2)
        yield writer.emit_log_with_standard_logging(log_data, "  OK.")

      yield writer.emit_end(ok=True, data={"processed": total, "total": total})

    except Exception as e:
      yield writer.emit_end(ok=False, error=str(e), data={})

    finally:
      writer.finalize()
      await log_function_footer(log_data)

  return StreamingResponse(stream_generator(), media_type="text/event-stream")
