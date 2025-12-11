import datetime, glob, json, os, re, typing
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

from hardcoded_config import CRAWLER_HARDCODED_CONFIG


# ----------------------------------------- START: V1A Streaming ------------------------------------------

# Get state folder path for streaming operations, creating if needed
def get_streaming_state_folder(persistent_storage_path: str) -> str:
  if not persistent_storage_path: return None
  state_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER)
  os.makedirs(state_folder, exist_ok=True)
  return state_folder

# Generate unique operation ID: endpoint_YYYY-MM-DD_HH-MM-SS_pPROCESS_rREQUEST
def generate_streaming_operation_id(endpoint_name: str, log_data: Dict[str, Any]) -> str:
  now = datetime.datetime.now()
  process_id = os.getpid()
  request_number = log_data.get('request_number', 0)
  return f"{endpoint_name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}_p{process_id}_r{request_number}"

# Get full path to state file
def get_streaming_state_file_path(state_folder: str, operation_id: str, state: str) -> str:
  if not state_folder: return None
  return os.path.join(state_folder, f"{operation_id}.{state}")

# Create a state file for an operation
def create_streaming_state_file(state_folder: str, operation_id: str, state: str) -> bool:
  file_path = get_streaming_state_file_path(state_folder, operation_id, state)
  if not file_path: return False
  with open(file_path, 'w') as f:
    f.write(datetime.datetime.now().isoformat())
  return True

# Delete a state file if it exists
def delete_streaming_state_file(state_folder: str, operation_id: str, state: str) -> bool:
  file_path = get_streaming_state_file_path(state_folder, operation_id, state)
  if not file_path or not os.path.exists(file_path): return False
  os.unlink(file_path)
  return True

# Check if a state file exists
def streaming_state_file_exists(state_folder: str, operation_id: str, state: str) -> bool:
  file_path = get_streaming_state_file_path(state_folder, operation_id, state)
  return file_path and os.path.exists(file_path)

# Rename state file from one state to another
def rename_streaming_state_file(state_folder: str, operation_id: str, from_state: str, to_state: str) -> bool:
  from_path = get_streaming_state_file_path(state_folder, operation_id, from_state)
  to_path = get_streaming_state_file_path(state_folder, operation_id, to_state)
  if not from_path or not to_path or not os.path.exists(from_path): return False
  os.rename(from_path, to_path)
  return True

# Get current state of an operation (only running or paused are valid active states)
def get_streaming_current_state(state_folder: str, operation_id: str) -> str:
  if streaming_state_file_exists(state_folder, operation_id, "running"): return "running"
  if streaming_state_file_exists(state_folder, operation_id, "paused"): return "paused"
  return None

# List all active streaming operations (only running or paused)
def list_streaming_operations(state_folder: str, endpoint_filter: str = None) -> List[Dict[str, str]]:
  if not state_folder: return []
  operations = {}
  for state in ["running", "paused"]:
    pattern = os.path.join(state_folder, f"*.{state}")
    for file_path in glob.glob(pattern):
      filename = os.path.basename(file_path)
      operation_id = filename.rsplit('.', 1)[0]
      if endpoint_filter and not operation_id.startswith(endpoint_filter): continue
      operations[operation_id] = state
  return [{"operation_id": op_id, "state": state} for op_id, state in operations.items()]

# ----------------------------------------- END: V1A Streaming ------------------------------------------


# ----------------------------------------- START: V1B Streaming -----------------------------------------

# Type aliases for V2 streaming
StreamingJobResult = Literal["ok", "partial", "cancelled", "fail"] 
StreamingJobState = Literal["running", "paused", "completed", "cancelled"]
StreamingJobControlState = Literal["pause_requested", "resume_requested", "cancel_requested"]

@dataclass
class StreamingJob:
  id: int                                                         # Unique streaming job identifier (1 ... n)
  router: str                                                     # Router name (e.g., 'testrouter2', 'crawler')
  endpoint: str                                                   # Endpoint name (e.g., 'streaming01')
  state: StreamingJobState                                        # Current job state
  started: datetime.datetime                                      # Timestamp when job started
  finished: datetime.datetime | None                              # Timestamp when job finished (None if active)
  source_url: str = ""                                            # Url to source endpoint that started this job
  monitor_url: str = ""                                           # Url to monitor endpoint
  total: int = 0                                                  # Total number of items to process
  current: int = 0                                                # Current item index (1-based)
  result: StreamingJobResult | None = None                        # Final result (None if still active)
  result_data: Any | None = None                                  # Additional result data (e.g., error details, stats)

# Derive sets from type aliases to avoid duplication
VALID_JOB_STATES = set(typing.get_args(StreamingJobState))
VALID_CONTROL_STATES = set(typing.get_args(StreamingJobControlState))
ALL_VALID_STATES = VALID_JOB_STATES | VALID_CONTROL_STATES

# Generate next streaming job ID by scanning existing files. Returns sequential integer starting at 1.
def generate_streaming_job_id(persistent_storage_path: str) -> int:
  jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER)
  os.makedirs(jobs_folder, exist_ok=True)
  
  # Get all job files recursively
  pattern = os.path.join(jobs_folder, "**", "*.*")
  all_files = glob.glob(pattern, recursive=True)
  
  # Filter only job files with valid extensions
  job_files = [f for f in all_files if os.path.splitext(f)[1][1:] in ALL_VALID_STATES]
  if not job_files: return 1
  
  # Sort by modification time (newest first) and take last 1000
  job_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
  recent_files = job_files[:1000]
  
  # Extract sj_id from filenames and find max
  # Filename format: TIMESTAMP_ENDPOINT_SJ_ID.state
  max_sj_id = 0
  for filepath in recent_files:
    filename = os.path.basename(filepath)
    match = re.match(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_[^_]+_(\d+)\.', filename)
    if match:
      sj_id = int(match.group(1))
      max_sj_id = max(max_sj_id, sj_id)
  
  return max_sj_id + 1

# Get folder path for streaming job files: PERSISTENT_STORAGE_PATH/jobs/[router]/[endpoint]/
def get_streaming_job_folder(persistent_storage_path: str, router_name: str, endpoint_name: str) -> str:
  folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER, router_name, endpoint_name)
  os.makedirs(folder, exist_ok=True)
  return folder

# Build full path to streaming job file: [folder]/[timestamp]_[endpoint]_[sj_id].[state]
def get_streaming_job_file_path(persistent_storage_path: str, router_name: str, endpoint_name: str, sj_id: int, state: str, timestamp: str = None) -> str:
  folder = get_streaming_job_folder(persistent_storage_path, router_name, endpoint_name)
  if timestamp: return os.path.join(folder, f"{timestamp}_{endpoint_name}_{sj_id}.{state}")
  else: return os.path.join(folder, f"*_{endpoint_name}_{sj_id}.{state}")

# Create streaming job file with metadata header. Uses exclusive mode to handle race conditions. Returns (success, timestamp).
def create_streaming_job_file(persistent_storage_path: str, router_name: str, endpoint_name: str, sj_id: int, state: str = "running") -> Tuple[bool, str]:
  timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
  file_path = get_streaming_job_file_path(persistent_storage_path, router_name, endpoint_name, sj_id, state, timestamp)
  
  try:
    with open(file_path, 'x', encoding='utf-8') as f:
      pass  # Create empty file
    return True, timestamp
  except FileExistsError:
    return False, ""

# Find streaming job file by sj_id and state. Returns full path or None.
def find_streaming_job_file(persistent_storage_path: str, router_name: str, endpoint_name: str, sj_id: int, state: str) -> Optional[str]:
  folder = get_streaming_job_folder(persistent_storage_path, router_name, endpoint_name)
  pattern = os.path.join(folder, f"*_{endpoint_name}_{sj_id}.{state}")
  matches = glob.glob(pattern)
  return matches[0] if matches else None

# Create control file (pause_requested, resume_requested, cancel_requested) for a streaming job.
def create_streaming_job_control_file(persistent_storage_path: str, router_name: str, endpoint_name: str, sj_id: int, timestamp: str, control_state: str) -> bool:
  folder = get_streaming_job_folder(persistent_storage_path, router_name, endpoint_name)
  file_path = os.path.join(folder, f"{timestamp}_{endpoint_name}_{sj_id}.{control_state}")
  
  try:
    with open(file_path, 'x', encoding='utf-8') as f:
      f.write(datetime.datetime.now().isoformat())
    return True
  except FileExistsError:
    return False

# Append message to streaming job log file. Writes to .running or .paused file.
def write_streaming_job_log(persistent_storage_path: str, router_name: str, endpoint_name: str, sj_id: int, message: str):
  for state in ["running", "paused"]:
    log_file = find_streaming_job_file(persistent_storage_path, router_name, endpoint_name, sj_id, state)
    if log_file:
      with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message)
        f.flush()
      return
  raise FileNotFoundError(f"No job file found for sj_id={sj_id}")

# Rename streaming job file from old_state to new_state.
def rename_streaming_job_file(persistent_storage_path: str, router_name: str, endpoint_name: str, sj_id: int, old_state: str, new_state: str) -> bool:
  old_path = find_streaming_job_file(persistent_storage_path, router_name, endpoint_name, sj_id, old_state)
  if not old_path: return False
  new_path = old_path.rsplit('.', 1)[0] + f".{new_state}"
  try:
    os.rename(old_path, new_path)
    return True
  except (FileNotFoundError, OSError):
    return False

# Delete streaming job state file by sj_id and state.
def delete_streaming_job_file(persistent_storage_path: str, router_name: str, endpoint_name: str, sj_id: int, state: str) -> bool:
  file_path = find_streaming_job_file(persistent_storage_path, router_name, endpoint_name, sj_id, state)
  if not file_path: return False
  try:
    os.remove(file_path)
    return True
  except FileNotFoundError:
    return False

# Check if streaming job state file exists.
def streaming_job_file_exists(persistent_storage_path: str, router_name: str, endpoint_name: str, sj_id: int, state: str) -> bool:
  return find_streaming_job_file(persistent_storage_path, router_name, endpoint_name, sj_id, state) is not None

# Get current state of streaming job (running, paused, completed, cancelled, or None).
def get_streaming_job_current_state(persistent_storage_path: str, router_name: str, endpoint_name: str, sj_id: int) -> Optional[str]:
  for state in ["running", "paused", "completed", "cancelled"]:
    if find_streaming_job_file(persistent_storage_path, router_name, endpoint_name, sj_id, state): return state
  return None

# Find streaming job by sj_id across all routers/endpoints. Returns dict with router_name, endpoint_name, state, file_path, timestamp or None.
def find_streaming_job_by_id(persistent_storage_path: str, sj_id: int) -> Optional[Dict]:
  jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER)
  if not os.path.exists(jobs_folder): return None
  
  for root, dirs, files in os.walk(jobs_folder):
    for f in files:
      match = re.match(r'^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_([^_]+)_(\d+)\.(\w+)$', f)
      if match:
        file_timestamp, file_endpoint, file_sj_id, file_state = match.group(1), match.group(2), int(match.group(3)), match.group(4)
        if file_sj_id == sj_id and file_state in VALID_JOB_STATES:
          rel_path = os.path.relpath(root, jobs_folder)
          parts = rel_path.split(os.sep)
          if len(parts) >= 2:
            return {"sj_id": sj_id, "router_name": parts[0], "endpoint_name": parts[1], "state": file_state, "timestamp": file_timestamp, "file_path": os.path.join(root, f)}
  return None

# List all streaming jobs with optional filters. Returns list of StreamingJob instances.
def list_streaming_jobs(persistent_storage_path: str, router_filter: Optional[str] = None, endpoint_filter: Optional[str] = None, state_filter: Optional[str] = None) -> List[StreamingJob]:
  jobs_folder = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_LOGS_SUBFOLDER)
  if not os.path.exists(jobs_folder): return []
  
  jobs = []
  for root, dirs, files in os.walk(jobs_folder):
    for f in files:
      match = re.match(r'^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_([^_]+)_(\d+)\.(running|paused|completed|cancelled)$', f)
      if not match: continue
      
      file_timestamp, file_endpoint, sj_id, state = match.group(1), match.group(2), int(match.group(3)), match.group(4)
      rel_path = os.path.relpath(root, jobs_folder)
      parts = rel_path.split(os.sep)
      if len(parts) < 2: continue
      
      router_name, endpoint_name = parts[0], parts[1]
      if router_filter and router_name != router_filter: continue
      if endpoint_filter and endpoint_name != endpoint_filter: continue
      if state_filter and state != state_filter: continue
      
      # Parse timestamp to datetime
      date_part, time_part = file_timestamp.split('_')
      started_str = f"{date_part}T{time_part.replace('-', ':')}"
      started = datetime.datetime.fromisoformat(started_str)
      
      # Read finished timestamp from log file if job is completed/cancelled
      finished = None
      if state in ['completed', 'cancelled']:
        file_path = os.path.join(root, f)
        try:
          with open(file_path, 'r', encoding='utf-8') as log_file:
            content = log_file.read()
            # Extract end_json section
            if '<end_json>' in content and '</end_json>' in content:
              start_idx = content.index('<end_json>') + len('<end_json>')
              end_idx = content.index('</end_json>')
              json_str = content[start_idx:end_idx].strip()
              end_data = json.loads(json_str)
              if end_data.get('finished'):
                finished = datetime.datetime.fromisoformat(end_data['finished'])
        except Exception:
          pass  # If parsing fails, leave finished as None
      
      # Create StreamingJob instance
      job = StreamingJob(
        id=sj_id,
        router=router_name,
        endpoint=endpoint_name,
        state=state,
        started=started,
        finished=finished
      )
      jobs.append(job)
  
  jobs.sort(key=lambda j: j.id, reverse=True)
  return jobs

# ----------------------------------------- END: V1B Streaming -------------------------------------------
