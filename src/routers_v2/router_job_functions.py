import asyncio, datetime, glob, json, os, re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import log_function_output

# Type definitions
JobState = Literal["running", "paused", "completed", "cancelled"]
ControlState = Literal["pause_requested", "resume_requested", "cancel_requested"]

VALID_JOB_STATES = {"running", "paused", "completed", "cancelled"}
VALID_CONTROL_STATES = {"pause_requested", "resume_requested", "cancel_requested"}
ALL_VALID_STATES = VALID_JOB_STATES | VALID_CONTROL_STATES

@dataclass
class JobMetadata:
  job_id: str                           # "jb_42"
  state: JobState
  source_url: str                       # "/v2/crawler/crawl?domain_id=TEST01&format=stream"
  monitor_url: str                      # "/v2/jobs/monitor?job_id=jb_42&format=stream"
  started_utc: str                      # ISO 8601: "2025-01-15T14:20:30.000000Z"
  finished_utc: str | None              # ISO 8601 or None if running
  result: dict | None                   # {ok, error, data} or None if running

class ControlAction(Enum):
  CANCEL = "cancel"

# ----------------------------------------- START: Job ID Generation ------------------------------------------------

# Generate next job ID number by scanning existing files. Returns sequential integer starting at 1.
def generate_job_id_number(persistent_storage_path: str) -> int:
  jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER)
  os.makedirs(jobs_folder, exist_ok=True)
  
  pattern = os.path.join(jobs_folder, "**", "*.*")
  all_files = glob.glob(pattern, recursive=True)
  
  job_files = [f for f in all_files if os.path.splitext(f)[1][1:] in ALL_VALID_STATES]
  if not job_files: return 1
  
  job_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
  recent_files = job_files[:1000]
  
  max_jb_id = 0
  for filepath in recent_files:
    filename = os.path.basename(filepath)
    match = re.search(r'\[jb_(\d+)\]', filename)
    if match:
      jb_id = int(match.group(1))
      max_jb_id = max(max_jb_id, jb_id)
  
  return max_jb_id + 1

# Generate job_id string: 'jb_[NUMBER]'
def generate_job_id(persistent_storage_path: str) -> str:
  return f"jb_{generate_job_id_number(persistent_storage_path)}"

# ----------------------------------------- END: Job ID Generation --------------------------------------------------


# ----------------------------------------- START: Job File Operations ----------------------------------------------

# Get folder path for streaming job files: PERSISTENT_STORAGE_PATH/jobs/[router]/
def get_job_folder(persistent_storage_path: str, router_name: str) -> str:
  folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER, router_name)
  os.makedirs(folder, exist_ok=True)
  return folder

# Build job filename: [TIMESTAMP]_[[ACTION]]_[[JB_ID]]_[[OBJECT_ID]].[state] or [TIMESTAMP]_[[ACTION]]_[[JB_ID]].[state]
def build_job_filename(timestamp: str, action: str, job_id: str, object_id: Optional[str], state: str) -> str:
  jb_number = job_id.replace("jb_", "")
  if object_id: return f"{timestamp}_[{action}]_[jb_{jb_number}]_[{object_id}].{state}"
  else: return f"{timestamp}_[{action}]_[jb_{jb_number}].{state}"

# Parse job filename to extract components. Returns dict or None if not a valid job file.
def parse_job_filename(filename: str) -> Optional[Dict]:
  pattern = r'^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_\[([^\]]+)\]_\[jb_(\d+)\](?:_\[([^\]]+)\])?\.(\w+)$'
  match = re.match(pattern, filename)
  if not match: return None
  timestamp, action, jb_number, object_id, state = match.groups()
  return {"timestamp": timestamp, "action": action, "job_id": f"jb_{jb_number}", "object_id": object_id, "state": state}

# Find job file by job_id across all routers. Returns dict with path, router_name, parsed info or None.
def find_job_file(persistent_storage_path: str, job_id: str, state: Optional[str] = None) -> Optional[Dict]:
  jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER)
  if not os.path.exists(jobs_folder): return None
  
  states_to_check = [state] if state else list(VALID_JOB_STATES)
  
  for root, dirs, files in os.walk(jobs_folder):
    for f in files:
      parsed = parse_job_filename(f)
      if parsed and parsed["job_id"] == job_id and parsed["state"] in states_to_check:
        rel_path = os.path.relpath(root, jobs_folder)
        router_name = rel_path.split(os.sep)[0] if rel_path != "." else ""
        return {"file_path": os.path.join(root, f), "router_name": router_name, **parsed}
  return None

# Create job file with exclusive mode to handle race conditions. Returns (success, file_path).
def create_job_file(persistent_storage_path: str, router_name: str, action: str, job_id: str, object_id: Optional[str], state: str = "running") -> Tuple[bool, str]:
  folder = get_job_folder(persistent_storage_path, router_name)
  timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
  filename = build_job_filename(timestamp, action, job_id, object_id, state)
  file_path = os.path.join(folder, filename)
  
  try:
    with open(file_path, 'x', encoding='utf-8') as f:
      pass
    return True, file_path
  except FileExistsError:
    return False, ""

# Rename job file from old_state to new_state.
def rename_job_file(file_path: str, new_state: str) -> Optional[str]:
  if not os.path.exists(file_path): return None
  base, old_ext = os.path.splitext(file_path)
  new_path = f"{base}.{new_state}"
  try:
    os.rename(file_path, new_path)
    return new_path
  except (FileNotFoundError, OSError):
    return None

# ----------------------------------------- END: Job File Operations ------------------------------------------------


# ----------------------------------------- START: Control File Operations ------------------------------------------

# Create control file for a job. Returns path to control file or None.
def create_control_file(persistent_storage_path: str, job_id: str, control_state: ControlState) -> Optional[str]:
  job_info = find_job_file(persistent_storage_path, job_id)
  if not job_info: return None
  
  folder = os.path.dirname(job_info["file_path"])
  timestamp = job_info["timestamp"]
  action = job_info["action"]
  object_id = job_info["object_id"]
  
  jb_number = job_id.replace("jb_", "")
  if object_id: filename = f"{timestamp}_[{action}]_[jb_{jb_number}]_[{object_id}].{control_state}"
  else: filename = f"{timestamp}_[{action}]_[jb_{jb_number}].{control_state}"
  
  control_path = os.path.join(folder, filename)
  try:
    with open(control_path, 'x', encoding='utf-8') as f:
      f.write(datetime.datetime.now(datetime.timezone.utc).isoformat())
    return control_path
  except FileExistsError:
    return None

# Check if control file exists for a job.
def control_file_exists(persistent_storage_path: str, job_id: str, control_state: ControlState) -> bool:
  job_info = find_job_file(persistent_storage_path, job_id)
  if not job_info: return False
  
  folder = os.path.dirname(job_info["file_path"])
  timestamp = job_info["timestamp"]
  action = job_info["action"]
  object_id = job_info["object_id"]
  
  jb_number = job_id.replace("jb_", "")
  if object_id: filename = f"{timestamp}_[{action}]_[jb_{jb_number}]_[{object_id}].{control_state}"
  else: filename = f"{timestamp}_[{action}]_[jb_{jb_number}].{control_state}"
  
  return os.path.exists(os.path.join(folder, filename))

# Delete control file for a job.
def delete_control_file(persistent_storage_path: str, job_id: str, control_state: ControlState) -> bool:
  job_info = find_job_file(persistent_storage_path, job_id)
  if not job_info: return False
  
  folder = os.path.dirname(job_info["file_path"])
  timestamp = job_info["timestamp"]
  action = job_info["action"]
  object_id = job_info["object_id"]
  
  jb_number = job_id.replace("jb_", "")
  if object_id: filename = f"{timestamp}_[{action}]_[jb_{jb_number}]_[{object_id}].{control_state}"
  else: filename = f"{timestamp}_[{action}]_[jb_{jb_number}].{control_state}"
  
  control_path = os.path.join(folder, filename)
  try:
    os.remove(control_path)
    return True
  except FileNotFoundError:
    return False

# ----------------------------------------- END: Control File Operations --------------------------------------------


# ----------------------------------------- START: StreamingJobWriter Class -----------------------------------------

class StreamingJobWriter:
  """Buffered writer for streaming job files. Handles dual output to HTTP and file."""
  
  def __init__(self, persistent_storage_path: str, router_name: str, action: str, object_id: Optional[str], source_url: str, buffer_size: int = None):
    """
    Create job file and initialize writer.
    - Generates unique job_id (jb_[NUMBER])
    - Creates job file: [TIMESTAMP]_[[ACTION]]_[[JB_ID]]_[[OBJECT_ID]].running
    - Retries with new job_id on collision (STREAM-FR-02)
    """
    if buffer_size is None: buffer_size = CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE
    
    self._persistent_storage_path = persistent_storage_path
    self._router_name = router_name
    self._action = action
    self._object_id = object_id
    self._source_url = source_url
    self._buffer_size = buffer_size
    self._buffer: List[str] = []
    self._file_path: str = ""
    self._job_id: str = ""
    self._started_utc: str = ""
    self._finished_utc: Optional[str] = None
    self._state: JobState = "running"
    self._end_emitted: bool = False
    
    max_retries = 3
    for attempt in range(max_retries):
      self._job_id = generate_job_id(persistent_storage_path)
      success, self._file_path = create_job_file(persistent_storage_path, router_name, action, self._job_id, object_id, "running")
      if success:
        self._started_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        break
    
    if not self._file_path: raise RuntimeError(f"Failed to create job file after {max_retries} retries")
  
  @property
  def job_id(self) -> str:
    return self._job_id
  
  @property
  def monitor_url(self) -> str:
    return f"/v2/jobs/monitor?job_id={self._job_id}&format=stream"
  
  @property
  def file_path(self) -> str:
    return self._file_path
  
  def _get_job_metadata(self) -> Dict:
    return {
      "job_id": self._job_id,
      "state": self._state,
      "source_url": self._source_url,
      "monitor_url": self.monitor_url,
      "started_utc": self._started_utc,
      "finished_utc": self._finished_utc,
      "result": None
    }
  
  def _flush_buffer(self) -> None:
    if not self._buffer or not self._file_path: return
    with open(self._file_path, 'a', encoding='utf-8') as f:
      f.write("".join(self._buffer))
      f.flush()
    self._buffer.clear()
  
  def _write_to_file(self, content: str, immediate: bool = False) -> None:
    self._buffer.append(content)
    if immediate or len(self._buffer) >= self._buffer_size:
      self._flush_buffer()
  
  def emit_start(self) -> str:
    """Emit start_json event. Immediate flush to file. (STREAM-FR-03)"""
    metadata = self._get_job_metadata()
    sse_content = f"event: start_json\ndata: {json.dumps(metadata)}\n\n"
    self._write_to_file(sse_content, immediate=True)
    return sse_content
  
  def emit_log(self, message: str) -> str:
    """Emit log event. Buffered write to file. (STREAM-FR-03)"""
    lines = message.split('\n')
    data_lines = '\n'.join(f"data: {line}" for line in lines)
    sse_content = f"event: log\n{data_lines}\n\n"
    self._write_to_file(sse_content)
    return sse_content
  
  def emit_log_with_standard_logging(self, log_data: Dict[str, Any], message: str) -> str:
    """Emit log event and also write to standard logging. (STREAM-FR-03, STREAM-FR-09)"""
    log_function_output(log_data, message)
    return self.emit_log(message)
  
  def emit_end(self, ok: bool, error: str = "", data: dict = None) -> str:
    """Emit end_json event. Immediate flush to file. (STREAM-FR-03, STREAM-FR-07)"""
    self._finished_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if data is None: data = {}
    
    result = {"ok": ok, "error": error, "data": data}
    
    if ok: self._state = "completed"
    elif error == "Cancelled by user": self._state = "cancelled"
    else: self._state = "completed"
    
    metadata = self._get_job_metadata()
    metadata["result"] = result
    
    sse_content = f"event: end_json\ndata: {json.dumps(metadata)}\n\n"
    self._write_to_file(sse_content, immediate=True)
    self._end_emitted = True
    return sse_content
  
  async def check_control(self) -> Tuple[List[str], Optional[ControlAction]]:
    """
    Check for control files and handle pause loop. (STREAM-FR-04, STREAM-FR-05)
    Returns (log_events, control_action):
    - log_events: list of SSE-formatted strings for pause/resume
    - control_action: ControlAction.CANCEL if cancelled, None otherwise
    """
    self._flush_buffer()
    log_events: List[str] = []
    
    if self._check_control_file("cancel_requested"):
      self._delete_control_file("cancel_requested")
      log_event = self.emit_log("  Cancel requested, stopping...")
      log_events.append(log_event)
      return log_events, ControlAction.CANCEL
    
    if self._check_control_file("pause_requested"):
      self._delete_control_file("pause_requested")
      log_event = self.emit_log("  Pause requested, pausing...")
      log_events.append(log_event)
      self._state = "paused"
      self._file_path = rename_job_file(self._file_path, "paused") or self._file_path
      
      while True:
        if self._check_control_file("cancel_requested"):
          self._delete_control_file("cancel_requested")
          log_event = self.emit_log("  Cancel requested while paused, stopping...")
          log_events.append(log_event)
          return log_events, ControlAction.CANCEL
        
        if self._check_control_file("resume_requested"):
          self._delete_control_file("resume_requested")
          log_event = self.emit_log("  Resume requested, resuming...")
          log_events.append(log_event)
          self._state = "running"
          self._file_path = rename_job_file(self._file_path, "running") or self._file_path
          break
        
        await asyncio.sleep(0.1)
    
    return log_events, None
  
  def _check_control_file(self, control_state: str) -> bool:
    folder = os.path.dirname(self._file_path)
    base_name = os.path.basename(self._file_path)
    base_without_ext = os.path.splitext(base_name)[0]
    control_path = os.path.join(folder, f"{base_without_ext}.{control_state}")
    return os.path.exists(control_path)
  
  def _delete_control_file(self, control_state: str) -> bool:
    folder = os.path.dirname(self._file_path)
    base_name = os.path.basename(self._file_path)
    base_without_ext = os.path.splitext(base_name)[0]
    control_path = os.path.join(folder, f"{base_without_ext}.{control_state}")
    try:
      os.remove(control_path)
      return True
    except FileNotFoundError:
      return False
  
  def finalize(self) -> None:
    """Finalize job file state. (STREAM-FR-06, STREAM-FR-07)"""
    self._flush_buffer()
    if self._end_emitted:
      final_state = "cancelled" if self._state == "cancelled" else "completed"
      if not self._file_path.endswith(f".{final_state}"):
        self._file_path = rename_job_file(self._file_path, final_state) or self._file_path

# ----------------------------------------- END: StreamingJobWriter Class -------------------------------------------


# ----------------------------------------- START: Job Query Functions ----------------------------------------------

# Find job by job_id across all routers. Returns JobMetadata or None.
def find_job_by_id(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  job_info = find_job_file(persistent_storage_path, job_id)
  if not job_info: return None
  return get_job_metadata(persistent_storage_path, job_id)

# List all jobs. Returns list of JobMetadata, newest first.
def list_jobs(persistent_storage_path: str, router_filter: str = None, state_filter: str = None) -> List[JobMetadata]:
  jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER)
  if not os.path.exists(jobs_folder): return []
  
  jobs = []
  for root, dirs, files in os.walk(jobs_folder):
    for f in files:
      parsed = parse_job_filename(f)
      if not parsed or parsed["state"] not in VALID_JOB_STATES: continue
      
      rel_path = os.path.relpath(root, jobs_folder)
      router_name = rel_path.split(os.sep)[0] if rel_path != "." else ""
      
      if router_filter and router_name != router_filter: continue
      if state_filter and parsed["state"] != state_filter: continue
      
      job_metadata = get_job_metadata(persistent_storage_path, parsed["job_id"])
      if job_metadata: jobs.append(job_metadata)
  
  jobs.sort(key=lambda j: j.started_utc, reverse=True)
  return jobs

# Parse job file and return JobMetadata from start_json/end_json.
def get_job_metadata(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  job_info = find_job_file(persistent_storage_path, job_id)
  if not job_info: return None
  
  file_path = job_info["file_path"]
  try:
    with open(file_path, 'r', encoding='utf-8') as f:
      content = f.read()
  except Exception:
    return None
  
  start_data = None
  end_data = None
  
  start_match = re.search(r'event: start_json\ndata: (.+)\n', content)
  if start_match:
    try:
      start_data = json.loads(start_match.group(1))
    except json.JSONDecodeError:
      pass
  
  end_match = re.search(r'event: end_json\ndata: (.+)\n', content)
  if end_match:
    try:
      end_data = json.loads(end_match.group(1))
    except json.JSONDecodeError:
      pass
  
  if start_data:
    return JobMetadata(
      job_id=start_data.get("job_id", job_id),
      state=end_data.get("state", start_data.get("state", job_info["state"])) if end_data else start_data.get("state", job_info["state"]),
      source_url=start_data.get("source_url", ""),
      monitor_url=start_data.get("monitor_url", f"/v2/jobs/monitor?job_id={job_id}&format=stream"),
      started_utc=start_data.get("started_utc", ""),
      finished_utc=end_data.get("finished_utc") if end_data else None,
      result=end_data.get("result") if end_data else None
    )
  
  return None

# Read full SSE content from job file for monitoring.
def read_job_log(persistent_storage_path: str, job_id: str) -> Optional[str]:
  job_info = find_job_file(persistent_storage_path, job_id)
  if not job_info: return None
  
  try:
    with open(job_info["file_path"], 'r', encoding='utf-8') as f:
      return f.read()
  except Exception:
    return None

# Extract result from end_json. Returns None if job not completed/cancelled.
def read_job_result(persistent_storage_path: str, job_id: str) -> Optional[dict]:
  metadata = get_job_metadata(persistent_storage_path, job_id)
  if metadata and metadata.result: return metadata.result
  return None

# ----------------------------------------- END: Job Query Functions ------------------------------------------------
