# Streaming Jobs V2 - Buffered writer for streaming job files
# Implements StreamingJobWriter class and job management functions per _V2_SPEC_ROUTERS.md specification

import asyncio, datetime, glob, json, os, re
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

from hardcoded_config import CRAWLER_HARDCODED_CONFIG

# Type definitions
JobState = Literal["running", "paused", "completed", "cancelled"]
ControlState = Literal["pause_requested", "resume_requested", "cancel_requested"]

# Job file extensions
JOB_STATES = ["running", "paused", "completed", "cancelled"]
CONTROL_STATES = ["pause_requested", "resume_requested", "cancel_requested"]

@dataclass
class JobMetadata:
  """Job metadata returned in start_json and end_json events."""
  job_id: str
  state: JobState
  source_url: str
  monitor_url: str
  started_utc: str
  finished_utc: Optional[str]
  result: Optional[dict]

class ControlAction(Enum):
  """Control actions returned by check_control()."""
  CANCEL = "cancel"

class StreamingJobWriter:
  """
  Buffered writer for streaming job files. Handles dual output to HTTP and file.
  
  Implements STREAM-FR-01 through STREAM-FR-08 and STREAM-IG-01 through STREAM-IG-06.
  
  Usage:
    writer = StreamingJobWriter(
      persistent_storage_path="/home/data",
      router_name="crawler",
      action="crawl",
      object_id="DOMAIN01",
      source_url="/v2/crawler/crawl?domain_id=DOMAIN01&format=stream",
      router_prefix="/v2"
    )
    yield writer.emit_start()
    yield writer.emit_log("Processing...")
    yield writer.emit_end(ok=True, data={"count": 10})
    writer.finalize()
  """
  
  def __init__(self, persistent_storage_path: str, router_name: str, action: str, object_id: Optional[str], source_url: str, router_prefix: str, buffer_size: int = None):
    """
    Create job file and initialize writer (STREAM-FR-02: atomic creation).
    - router_prefix: Injected from app.py (e.g., '/v2') for constructing monitor_url
    - Generates unique job_id (jb_[NUMBER])
    - Creates job file: [TIMESTAMP]_[[ACTION]]_[[JB_ID]]_[[OBJECT_ID]].running
    - Retries with new job_id on collision
    """
    self._persistent_storage_path = persistent_storage_path
    self._router_name = router_name
    self._action = action
    self._object_id = object_id
    self._source_url = source_url
    self._router_prefix = router_prefix
    self._buffer_size = buffer_size if buffer_size is not None else CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE
    
    self._started_utc = datetime.datetime.now(datetime.timezone.utc)
    self._finished_utc: Optional[datetime.datetime] = None
    self._final_state: Optional[JobState] = None
    self._buffer: list[str] = []
    self._job_id: str = ""
    self._job_file_path: str = ""
    self._file_handle = None
    
    # Create job directory
    self._jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER, router_name)
    os.makedirs(self._jobs_folder, exist_ok=True)
    
    # Generate job file with collision retry (STREAM-FR-02)
    self._create_job_file()
  
  def _create_job_file(self) -> None:
    """Create job file with atomic creation and collision retry."""
    max_retries = 5
    for attempt in range(max_retries):
      job_number = generate_job_number(self._persistent_storage_path)
      self._job_id = f"jb_{job_number}"
      
      timestamp = self._started_utc.strftime("%Y-%m-%d_%H-%M-%S")
      if self._object_id:
        filename = f"{timestamp}_[{self._action}]_[{self._job_id}]_[{self._object_id}].running"
      else:
        filename = f"{timestamp}_[{self._action}]_[{self._job_id}].running"
      
      self._job_file_path = os.path.join(self._jobs_folder, filename)
      
      try:
        # Exclusive creation (STREAM-FR-02)
        fd = os.open(self._job_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        self._file_handle = os.fdopen(fd, 'w', encoding='utf-8')
        return
      except FileExistsError:
        continue
    
    raise RuntimeError(f"Failed to create job file after {max_retries} attempts")
  
  @property
  def job_id(self) -> str:
    """Returns job_id string, e.g., 'jb_42'."""
    return self._job_id
  
  @property
  def monitor_url(self) -> str:
    """Returns monitor URL: {router_prefix}/jobs/monitor?job_id={job_id}&format=stream"""
    return f"{self._router_prefix}/jobs/monitor?job_id={self._job_id}&format=stream"
  
  def _format_sse_event(self, event_type: str, data: str) -> str:
    """Format SSE event with event type and data lines."""
    lines = data.split('\n')
    sse_lines = [f"event: {event_type}"]
    for line in lines:
      sse_lines.append(f"data: {line}")
    sse_lines.append("")
    sse_lines.append("")
    return '\n'.join(sse_lines)
  
  def _get_job_metadata(self, state: JobState, result: Optional[dict] = None) -> dict:
    """Build job metadata dictionary."""
    return {
      "job_id": self._job_id,
      "state": state,
      "source_url": self._source_url,
      "monitor_url": self.monitor_url,
      "started_utc": self._started_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
      "finished_utc": self._finished_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ") if self._finished_utc else None,
      "result": result
    }
  
  def emit_start(self) -> str:
    """
    Emit start_json event. Immediate flush to file (STREAM-FR-03, STREAM-IG-01).
    Returns SSE-formatted string for HTTP response.
    """
    metadata = self._get_job_metadata("running")
    sse = self._format_sse_event("start_json", json.dumps(metadata))
    self._write_immediate(sse)
    return sse
  
  def emit_log(self, message: str) -> str:
    """
    Emit log event. Buffered write to file (STREAM-FR-03).
    Message should already include timestamp from MiddlewareLogger.
    Returns SSE-formatted string for HTTP response.
    """
    sse = self._format_sse_event("log", message)
    self._write_buffered(sse)
    return sse
  
  def emit_end(self, ok: bool, error: str = "", data: dict = None, cancelled: bool = False) -> str:
    """
    Emit end_json event. Immediate flush to file (STREAM-FR-03, STREAM-FR-07, STREAM-IG-02).
    Sets finished_utc timestamp.
    - cancelled=False (default): state="completed", result.ok indicates success/failure
    - cancelled=True: state="cancelled" (for user-initiated cancellation)
    Returns SSE-formatted string for HTTP response.
    """
    self._finished_utc = datetime.datetime.now(datetime.timezone.utc)
    self._final_state = "cancelled" if cancelled else "completed"
    
    result = {"ok": ok, "error": error, "data": data if data is not None else {}}
    metadata = self._get_job_metadata(self._final_state, result)
    sse = self._format_sse_event("end_json", json.dumps(metadata))
    
    self._flush_buffer()
    self._write_immediate(sse)
    return sse
  
  def _write_immediate(self, content: str) -> None:
    """Write content immediately to file."""
    if self._file_handle:
      self._file_handle.write(content)
      self._file_handle.flush()
  
  def _write_buffered(self, content: str) -> None:
    """Add content to buffer, flush if buffer size reached."""
    self._buffer.append(content)
    if len(self._buffer) >= self._buffer_size:
      self._flush_buffer()
  
  def _flush_buffer(self) -> None:
    """Flush buffer to file."""
    if self._buffer and self._file_handle:
      self._file_handle.write(''.join(self._buffer))
      self._file_handle.flush()
      self._buffer.clear()
  
  async def check_control(self) -> tuple[list[str], Optional[ControlAction]]:
    """
    Check for control files and handle pause loop (STREAM-FR-04, STREAM-FR-05).
    - Flushes buffer before checking
    - If pause_requested: emits pause log, enters async pause loop, renames to .paused
    - If cancel_requested: returns ControlAction.CANCEL
    - If resume_requested (while paused): emits resume log, renames to .running
    Returns (log_events, control_action):
    - log_events: list of SSE-formatted strings for pause/resume
    - control_action: ControlAction.CANCEL if cancelled, None otherwise
    """
    self._flush_buffer()
    log_events: list[str] = []
    
    # Check for cancel first (highest priority)
    cancel_file = self._find_control_file("cancel_requested")
    if cancel_file:
      os.unlink(cancel_file)
      return (log_events, ControlAction.CANCEL)
    
    # Check for pause
    pause_file = self._find_control_file("pause_requested")
    if pause_file:
      os.unlink(pause_file)
      
      # Emit pause log with timestamp (not going through MiddlewareLogger)
      timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      sse = self.emit_log(f"[{timestamp}] Pause requested, pausing...")
      log_events.append(sse)
      
      # Rename to .paused
      paused_path = self._job_file_path.replace(".running", ".paused")
      self._close_file()
      os.rename(self._job_file_path, paused_path)
      self._job_file_path = paused_path
      self._file_handle = open(self._job_file_path, 'a', encoding='utf-8')
      
      # Enter pause loop (STREAM-FR-05)
      while True:
        await asyncio.sleep(1.0)
        
        # Check for cancel while paused
        cancel_file = self._find_control_file("cancel_requested")
        if cancel_file:
          os.unlink(cancel_file)
          return (log_events, ControlAction.CANCEL)
        
        # Check for resume
        resume_file = self._find_control_file("resume_requested")
        if resume_file:
          os.unlink(resume_file)
          
          # Emit resume log with timestamp (not going through MiddlewareLogger)
          timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          sse = self.emit_log(f"[{timestamp}] Resume requested, resuming...")
          log_events.append(sse)
          
          # Rename to .running
          running_path = self._job_file_path.replace(".paused", ".running")
          self._close_file()
          os.rename(self._job_file_path, running_path)
          self._job_file_path = running_path
          self._file_handle = open(self._job_file_path, 'a', encoding='utf-8')
          break
    
    return (log_events, None)
  
  def _find_control_file(self, control_type: str) -> Optional[str]:
    """Find control file matching this job_id."""
    pattern = os.path.join(self._jobs_folder, f"*[{self._job_id}]*.{control_type}")
    files = glob.glob(pattern)
    if files: return files[0]
    
    # Also check simpler pattern without object_id
    pattern = os.path.join(self._jobs_folder, f"*[{self._job_id}].{control_type}")
    files = glob.glob(pattern)
    return files[0] if files else None
  
  def _close_file(self) -> None:
    """Close file handle if open."""
    if self._file_handle:
      self._file_handle.close()
      self._file_handle = None
  
  def finalize(self) -> None:
    """
    Finalize job file state (STREAM-FR-06, STREAM-FR-07).
    - If end_json emitted: rename to .completed or .cancelled
    - Flushes any remaining buffer
    Called automatically in finally block.
    """
    self._flush_buffer()
    self._close_file()
    
    if self._final_state and os.path.exists(self._job_file_path):
      # Rename to final state
      final_path = re.sub(r'\.(running|paused)$', f'.{self._final_state}', self._job_file_path)
      if final_path != self._job_file_path:
        os.rename(self._job_file_path, final_path)
        self._job_file_path = final_path


# ----------------------------------------- START: Standalone functions for /v2/jobs endpoints --------------------------

def generate_job_id(persistent_storage_path: str) -> str:
  """Generate next job ID: 'jb_[NUMBER]'. Scans existing files to find max."""
  return f"jb_{generate_job_number(persistent_storage_path)}"

def generate_job_number(persistent_storage_path: str) -> int:
  """
  Generate next job number by scanning existing files to find max.
  Returns integer for use in 'jb_[NUMBER]' format.
  Scans most recent 1000 files for performance.
  """
  jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER)
  if not os.path.exists(jobs_folder): return 1
  
  # Find all job files recursively
  all_files = []
  for ext in JOB_STATES:
    all_files.extend(glob.glob(os.path.join(jobs_folder, "**", f"*.{ext}"), recursive=True))
  
  if not all_files: return 1
  
  # Sort by modification time (newest first), take first 1000
  all_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
  recent_files = all_files[:1000]
  
  # Extract job numbers using regex
  job_id_pattern = re.compile(r'\[jb_(\d+)\]')
  max_number = 0
  
  for filepath in recent_files:
    filename = os.path.basename(filepath)
    match = job_id_pattern.search(filename)
    if match:
      number = int(match.group(1))
      if number > max_number: max_number = number
  
  return max_number + 1

def find_job_file(persistent_storage_path: str, job_id: str) -> Optional[str]:
  """Find job file path by job_id across all routers. Returns path or None."""
  jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER)
  if not os.path.exists(jobs_folder): return None
  
  for ext in JOB_STATES:
    pattern = os.path.join(jobs_folder, "**", f"*[{job_id}]*.{ext}")
    files = glob.glob(pattern, recursive=True)
    if files: return files[0]
    
    pattern = os.path.join(jobs_folder, "**", f"*[{job_id}].{ext}")
    files = glob.glob(pattern, recursive=True)
    if files: return files[0]
  
  return None

def _parse_job_file(filepath: str) -> Optional[JobMetadata]:
  """Parse job file and extract metadata from start_json and end_json events."""
  if not os.path.exists(filepath): return None
  
  with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
  
  # Extract state from file extension
  ext = filepath.split('.')[-1]
  state: JobState = ext if ext in JOB_STATES else "running"
  
  # Parse start_json
  start_match = re.search(r'event: start_json\ndata: (.+?)(?=\n\n)', content, re.DOTALL)
  if not start_match: return None
  
  try:
    start_data = json.loads(start_match.group(1).replace('\ndata: ', ''))
  except json.JSONDecodeError:
    return None
  
  # Parse end_json if present
  end_data = None
  end_match = re.search(r'event: end_json\ndata: (.+?)(?=\n\n|$)', content, re.DOTALL)
  if end_match:
    try:
      end_data = json.loads(end_match.group(1).replace('\ndata: ', ''))
    except json.JSONDecodeError:
      pass
  
  return JobMetadata(
    job_id=start_data.get("job_id", ""),
    state=end_data.get("state", state) if end_data else state,
    source_url=start_data.get("source_url", ""),
    monitor_url=start_data.get("monitor_url", ""),
    started_utc=start_data.get("started_utc", ""),
    finished_utc=end_data.get("finished_utc") if end_data else None,
    result=end_data.get("result") if end_data else None
  )

def find_job_by_id(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  """Find job across all routers. Returns JobMetadata or None."""
  filepath = find_job_file(persistent_storage_path, job_id)
  if not filepath: return None
  return _parse_job_file(filepath)

def list_jobs(persistent_storage_path: str, router_filter: str = None, state_filter: str = None) -> list[JobMetadata]:
  """List all jobs. Returns list of JobMetadata, newest first."""
  jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER)
  if not os.path.exists(jobs_folder): return []
  
  # Build search path
  if router_filter:
    search_path = os.path.join(jobs_folder, router_filter)
  else:
    search_path = jobs_folder
  
  # Find all job files
  all_files = []
  states_to_search = [state_filter] if state_filter and state_filter in JOB_STATES else JOB_STATES
  for ext in states_to_search:
    all_files.extend(glob.glob(os.path.join(search_path, "**", f"*.{ext}"), recursive=True))
  
  # Sort by modification time (newest first)
  all_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
  
  # Parse each file
  jobs = []
  for filepath in all_files:
    metadata = _parse_job_file(filepath)
    if metadata: jobs.append(metadata)
  
  return jobs

def get_job_metadata(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  """Parse job file and return JobMetadata from start_json/end_json."""
  return find_job_by_id(persistent_storage_path, job_id)

def read_job_log(persistent_storage_path: str, job_id: str) -> str:
  """Read full SSE content from job file for monitoring."""
  filepath = find_job_file(persistent_storage_path, job_id)
  if not filepath: return ""
  
  with open(filepath, 'r', encoding='utf-8') as f:
    return f.read()

def read_job_result(persistent_storage_path: str, job_id: str) -> Optional[dict]:
  """Extract result from end_json. Returns None if job not completed/cancelled."""
  metadata = find_job_by_id(persistent_storage_path, job_id)
  if not metadata: return None
  return metadata.result

def create_control_file(persistent_storage_path: str, job_id: str, action: str) -> bool:
  """Create control file (.pause_requested, .resume_requested, .cancel_requested). Returns True if created."""
  if action not in ["pause", "resume", "cancel"]: return False
  
  # Find the job file to determine router folder
  job_filepath = find_job_file(persistent_storage_path, job_id)
  if not job_filepath: return False
  
  jobs_folder = os.path.dirname(job_filepath)
  control_filename = f"[{job_id}].{action}_requested"
  control_filepath = os.path.join(jobs_folder, control_filename)
  
  try:
    with open(control_filepath, 'w', encoding='utf-8') as f:
      f.write(f"{action}\n{datetime.datetime.now(datetime.timezone.utc).isoformat()}\n")
    return True
  except Exception:
    return False

def delete_job(persistent_storage_path: str, job_id: str) -> bool:
  """Delete job file. Returns True if deleted."""
  filepath = find_job_file(persistent_storage_path, job_id)
  if not filepath: return False
  
  try:
    os.unlink(filepath)
    return True
  except Exception:
    return False

# ----------------------------------------- END: Standalone functions for /v2/jobs endpoints ----------------------------
