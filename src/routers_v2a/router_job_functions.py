import asyncio, datetime, glob, json, os, re
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from utils import log_function_output


JobState = Literal["running", "paused", "completed", "cancelled"]
ControlState = Literal["pause_requested", "resume_requested", "cancel_requested"]


@dataclass
class JobMetadata:
  job_id: str
  state: JobState
  source_url: str
  monitor_url: str
  started_utc: str
  finished_utc: str | None
  result: dict | None


class ControlAction(Enum):
  CANCEL = "cancel"


def _utc_now_iso() -> str:
  return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _format_sse_event(event_name: str, data: str) -> str:
  lines = data.split("\n")
  data_lines = "".join([f"data: {line}\n" for line in lines])
  return f"event: {event_name}\n{data_lines}\n"


def _is_valid_job_state_extension(ext: str) -> bool:
  return ext in {"running", "paused", "completed", "cancelled"}


def _extract_job_number_from_filename(filename: str) -> Optional[int]:
  match = re.search(r"\[jb_(\d+)\]", filename)
  if not match: return None
  try: return int(match.group(1))
  except Exception: return None


def _extract_job_id_from_filename(filename: str) -> Optional[str]:
  match = re.search(r"\[(jb_\d+)\]", filename)
  if not match: return None
  return match.group(1)


def _parse_sse_events(sse_text: str) -> list[dict]:
  blocks = [b for b in sse_text.split("\n\n") if b.strip()]
  events = []
  for block in blocks:
    event_name = None
    data_lines = []
    for line in block.split("\n"):
      if line.startswith("event:"):
        event_name = line[len("event:"):].strip()
      elif line.startswith("data:"):
        data_lines.append(line[len("data:"):].lstrip())
    if event_name:
      events.append({"event": event_name, "data": "\n".join(data_lines)})
  return events


def _get_jobs_root(persistent_storage_path: str) -> str:
  return os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER)


def generate_job_id(persistent_storage_path: str) -> str:
  jobs_root = _get_jobs_root(persistent_storage_path)
  os.makedirs(jobs_root, exist_ok=True)

  all_files = glob.glob(os.path.join(jobs_root, "**", "*.*"), recursive=True)
  job_files = []
  for f in all_files:
    ext = os.path.splitext(f)[1][1:]
    if _is_valid_job_state_extension(ext): job_files.append(f)

  if not job_files: return "jb_1"

  job_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
  recent_files = job_files[:1000]

  max_num = 0
  for path in recent_files:
    n = _extract_job_number_from_filename(os.path.basename(path))
    if n is not None: max_num = max(max_num, n)

  return f"jb_{max_num + 1}"


def find_job_by_id(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  jobs_root = _get_jobs_root(persistent_storage_path)
  if not os.path.exists(jobs_root): return None

  all_files = glob.glob(os.path.join(jobs_root, "**", f"*[{job_id}]*.*"), recursive=True)
  candidates = []
  for f in all_files:
    ext = os.path.splitext(f)[1][1:]
    if _is_valid_job_state_extension(ext): candidates.append(f)

  if not candidates: return None
  candidates.sort(key=lambda f: os.path.getmtime(f), reverse=True)
  return get_job_metadata_from_file_path(persistent_storage_path, candidates[0])


def list_jobs(persistent_storage_path: str, router_filter: str = None, state_filter: str = None) -> list[JobMetadata]:
  jobs_root = _get_jobs_root(persistent_storage_path)
  if not os.path.exists(jobs_root): return []

  all_files = glob.glob(os.path.join(jobs_root, "**", "*.*"), recursive=True)
  job_files = []
  for f in all_files:
    ext = os.path.splitext(f)[1][1:]
    if not _is_valid_job_state_extension(ext):
      continue
    if state_filter and ext != state_filter:
      continue
    if router_filter:
      rel = os.path.relpath(f, jobs_root)
      if not rel.split(os.sep)[0] == router_filter:
        continue
    job_files.append(f)

  job_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)

  jobs = []
  for f in job_files:
    meta = get_job_metadata_from_file_path(persistent_storage_path, f)
    if meta:
      jobs.append(meta)

  return jobs


def get_job_metadata(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  meta = find_job_by_id(persistent_storage_path, job_id)
  return meta


def get_job_metadata_from_file_path(persistent_storage_path: str, file_path: str) -> Optional[JobMetadata]:
  try:
    state = os.path.splitext(file_path)[1][1:]
    if not _is_valid_job_state_extension(state):
      return None

    with open(file_path, "r", encoding="utf-8") as f:
      content = f.read()

    events = _parse_sse_events(content)
    start_json = next((e for e in events if e.get("event") == "start_json"), None)
    end_json = next((e for e in reversed(events) if e.get("event") == "end_json"), None)

    start_data = None
    if start_json and start_json.get("data"):
      try: start_data = json.loads(start_json["data"])
      except Exception: start_data = None

    end_data = None
    if end_json and end_json.get("data"):
      try: end_data = json.loads(end_json["data"])
      except Exception: end_data = None

    job_id_in_file = None
    if end_data and end_data.get("job_id"):
      job_id_in_file = end_data.get("job_id")
    elif start_data and start_data.get("job_id"):
      job_id_in_file = start_data.get("job_id")
    else:
      job_id_in_file = _extract_job_id_from_filename(os.path.basename(file_path))

    if not job_id_in_file:
      return None

    source_url = (start_data or {}).get("source_url", "")
    monitor_url = (start_data or {}).get("monitor_url", f"/v2a/jobs/monitor?job_id={job_id_in_file}&format=stream")
    started_utc = (start_data or {}).get("started_utc", "")

    finished_utc = None
    result = None

    if end_data:
      finished_utc = end_data.get("finished_utc")
      result = end_data.get("result")
      state = end_data.get("state", state)

    return JobMetadata(job_id=job_id_in_file, state=state, source_url=source_url, monitor_url=monitor_url, started_utc=started_utc, finished_utc=finished_utc, result=result)
  except Exception:
    return None


def read_job_log(persistent_storage_path: str, job_id: str) -> str:
  meta = find_job_by_id(persistent_storage_path, job_id)
  if not meta:
    return ""

  jobs_root = _get_jobs_root(persistent_storage_path)
  matches = glob.glob(os.path.join(jobs_root, "**", f"*[{job_id}]*.*"), recursive=True)
  candidates = []
  for f in matches:
    ext = os.path.splitext(f)[1][1:]
    if _is_valid_job_state_extension(ext): candidates.append(f)

  if not candidates:
    return ""

  candidates.sort(key=lambda f: os.path.getmtime(f), reverse=True)
  try:
    with open(candidates[0], "r", encoding="utf-8") as fp:
      return fp.read()
  except Exception:
    return ""


def read_job_result(persistent_storage_path: str, job_id: str) -> Optional[dict]:
  meta = find_job_by_id(persistent_storage_path, job_id)
  if not meta:
    return None
  return meta.result


def create_control_file(persistent_storage_path: str, job_id: str, action: str) -> bool:
  job_meta = find_job_by_id(persistent_storage_path, job_id)
  if not job_meta:
    return False

  jobs_root = _get_jobs_root(persistent_storage_path)
  matches = glob.glob(os.path.join(jobs_root, "**", f"*[{job_id}]*.*"), recursive=True)
  candidates = []
  for f in matches:
    ext = os.path.splitext(f)[1][1:]
    if _is_valid_job_state_extension(ext): candidates.append(f)

  if not candidates:
    return False

  candidates.sort(key=lambda f: os.path.getmtime(f), reverse=True)
  job_file_path = candidates[0]
  base, _ = os.path.splitext(job_file_path)

  control_state = None
  if action == "pause": control_state = "pause_requested"
  elif action == "resume": control_state = "resume_requested"
  elif action == "cancel": control_state = "cancel_requested"
  else: return False

  control_path = f"{base}.{control_state}"

  try:
    with open(control_path, "x", encoding="utf-8") as f:
      f.write(_utc_now_iso())
    return True
  except FileExistsError:
    return False
  except Exception:
    return False


def delete_job(persistent_storage_path: str, job_id: str) -> bool:
  jobs_root = _get_jobs_root(persistent_storage_path)
  matches = glob.glob(os.path.join(jobs_root, "**", f"*[{job_id}]*.*"), recursive=True)
  deleted_any = False
  for f in matches:
    ext = os.path.splitext(f)[1][1:]
    if _is_valid_job_state_extension(ext) or ext in {"pause_requested", "resume_requested", "cancel_requested"}:
      try:
        os.remove(f)
        deleted_any = True
      except Exception:
        pass
  return deleted_any


class StreamingJobWriter:

  def __init__(self, persistent_storage_path: str, router_name: str, action: str, object_id: Optional[str], source_url: str, buffer_size: int = CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE):
    self._persistent_storage_path = persistent_storage_path
    self._router_name = router_name
    self._action = action
    self._object_id = object_id
    self._source_url = source_url
    self._buffer_size = buffer_size

    self._job_id = None
    self._state: JobState = "running"
    self._started_utc = _utc_now_iso()
    self._finished_utc = None
    self._result = None
    self._buffer: list[str] = []
    self._job_file_path = None
    self._end_emitted = False
    self._cancel_requested = False

    self._create_job_file()

  @property
  def job_id(self) -> str:
    return self._job_id

  @property
  def monitor_url(self) -> str:
    return f"/v2/jobs/monitor?job_id={self._job_id}&format=stream"

  def emit_start(self) -> str:
    payload = {
      "job_id": self._job_id,
      "state": "running",
      "source_url": self._source_url,
      "monitor_url": self.monitor_url,
      "started_utc": self._started_utc,
      "finished_utc": None,
      "result": None
    }
    sse = _format_sse_event("start_json", json.dumps(payload, ensure_ascii=False))
    self._flush_buffer_to_file()
    self._write_to_file(sse)
    return sse

  def emit_log(self, message: str) -> str:
    sse = _format_sse_event("log", message)
    self._buffer.append(sse)
    if len(self._buffer) >= self._buffer_size:
      self._flush_buffer_to_file()
    return sse

  def emit_log_with_standard_logging(self, log_data, message: str) -> str:
    log_function_output(log_data, message)
    return self.emit_log(message)

  def emit_end(self, ok: bool, error: str = "", data: dict = None) -> str:
    self._finished_utc = _utc_now_iso()
    state: JobState = "cancelled" if self._cancel_requested else "completed"
    self._result = {"ok": bool(ok), "error": error or "", "data": {} if data is None else data}

    payload = {
      "job_id": self._job_id,
      "state": state,
      "source_url": self._source_url,
      "monitor_url": self.monitor_url,
      "started_utc": self._started_utc,
      "finished_utc": self._finished_utc,
      "result": self._result
    }

    sse = _format_sse_event("end_json", json.dumps(payload, ensure_ascii=False))
    self._flush_buffer_to_file()
    self._write_to_file(sse)
    self._end_emitted = True
    self._state = state
    return sse

  async def check_control(self) -> tuple[list[str], Optional[ControlAction]]:
    self._flush_buffer_to_file()

    control_logs: list[str] = []

    cancel_path = self._control_file_path("cancel_requested")
    pause_path = self._control_file_path("pause_requested")
    resume_path = self._control_file_path("resume_requested")

    if os.path.exists(cancel_path):
      self._cancel_requested = True
      self._try_delete_file(cancel_path)
      control_logs.append(self._emit_control_log_immediate("  Cancel requested, stopping..."))
      return control_logs, ControlAction.CANCEL

    if self._state == "running" and os.path.exists(pause_path):
      self._try_delete_file(pause_path)
      control_logs.append(self._emit_control_log_immediate("  Pause requested, pausing..."))
      self._rename_state("paused")
      self._state = "paused"

    while self._state == "paused":
      cancel_path = self._control_file_path("cancel_requested")
      resume_path = self._control_file_path("resume_requested")

      if os.path.exists(cancel_path):
        self._cancel_requested = True
        self._try_delete_file(cancel_path)
        control_logs.append(self._emit_control_log_immediate("  Cancel requested while paused, stopping..."))
        return control_logs, ControlAction.CANCEL

      if os.path.exists(resume_path):
        self._try_delete_file(resume_path)
        control_logs.append(self._emit_control_log_immediate("  Resume requested, resuming..."))
        self._rename_state("running")
        self._state = "running"
        break

      await asyncio.sleep(0.2)

    return control_logs, None

  def finalize(self) -> None:
    try:
      self._flush_buffer_to_file()
      if self._end_emitted:
        if self._state == "cancelled":
          self._rename_state("cancelled")
        else:
          self._rename_state("completed")
    except Exception:
      pass

  def _create_job_file(self) -> None:
    jobs_root = _get_jobs_root(self._persistent_storage_path)
    folder = os.path.join(jobs_root, self._router_name)
    os.makedirs(folder, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    for _ in range(10):
      job_id = generate_job_id(self._persistent_storage_path)
      base_parts = [timestamp, f"[{self._action}]", f"[{job_id}]"]
      if self._object_id:
        base_parts.append(f"[{self._object_id}]")
      base_name = "_".join(base_parts)
      file_path = os.path.join(folder, f"{base_name}.running")

      try:
        with open(file_path, "x", encoding="utf-8"):
          pass
        self._job_id = job_id
        self._job_file_path = file_path
        return
      except FileExistsError:
        continue

    raise RuntimeError("Failed to create job file due to repeated collisions")

  def _control_file_path(self, control_state: ControlState) -> str:
    base, _ = os.path.splitext(self._job_file_path)
    return f"{base}.{control_state}"

  def _emit_control_log_immediate(self, message: str) -> str:
    sse = _format_sse_event("log", message)
    self._flush_buffer_to_file()
    self._write_to_file(sse)
    return sse

  def _flush_buffer_to_file(self) -> None:
    if not self._buffer:
      return
    payload = "".join(self._buffer)
    self._buffer = []
    self._write_to_file(payload)

  def _write_to_file(self, text: str) -> None:
    if not self._job_file_path:
      return
    with open(self._job_file_path, "a", encoding="utf-8") as f:
      f.write(text)
      f.flush()

  def _rename_state(self, new_state: JobState) -> None:
    if not self._job_file_path:
      return
    base, _ = os.path.splitext(self._job_file_path)
    new_path = f"{base}.{new_state}"
    if self._job_file_path == new_path:
      return
    os.rename(self._job_file_path, new_path)
    self._job_file_path = new_path

  def _try_delete_file(self, path: str) -> None:
    try:
      os.remove(path)
    except Exception:
      pass
