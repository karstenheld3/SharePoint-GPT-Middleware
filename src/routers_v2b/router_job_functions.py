import asyncio, datetime, glob, json, os, re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Optional

from hardcoded_config import CRAWLER_HARDCODED_CONFIG

JobState = Literal["running", "paused", "completed", "cancelled"]
ControlState = Literal["pause_requested", "resume_requested", "cancel_requested"]

VALID_JOB_STATES: set[str] = {"running", "paused", "completed", "cancelled"}
VALID_CONTROL_STATES: set[str] = {"pause_requested", "resume_requested", "cancel_requested"}


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
  return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _get_jobs_root(persistent_storage_path: str) -> str:
  if not persistent_storage_path: raise ValueError("Expected a non-empty value for 'persistent_storage_path'.")
  jobs_root = os.path.join(persistent_storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER)
  os.makedirs(jobs_root, exist_ok=True)
  return jobs_root


def _iter_job_state_files(persistent_storage_path: str):
  jobs_root = _get_jobs_root(persistent_storage_path)
  for root, _, files in os.walk(jobs_root):
    for name in files:
      _, ext = os.path.splitext(name)
      ext = ext.lstrip(".")
      if ext in VALID_JOB_STATES:
        yield os.path.join(root, name)


def _extract_job_number_from_filename(filename: str) -> Optional[int]:
  match = re.search(r"\[jb_(\d+)\]", filename)
  if not match: return None
  try: return int(match.group(1))
  except Exception: return None


def generate_job_id(persistent_storage_path: str) -> str:
  job_files = list(_iter_job_state_files(persistent_storage_path))
  if not job_files: return "jb_1"

  job_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
  recent_files = job_files[:1000]

  max_id = 0
  for file_path in recent_files:
    number = _extract_job_number_from_filename(os.path.basename(file_path))
    if number is not None: max_id = max(max_id, number)

  return f"jb_{max_id + 1}"


def _parse_sse_event_json(full_text: str, event_name: str, last: bool = False) -> Optional[dict]:
  lines = full_text.splitlines()
  candidates = []
  i = 0
  while i < len(lines):
    if lines[i].strip() != f"event: {event_name}":
      i += 1
      continue

    i += 1
    data_lines = []
    while i < len(lines) and lines[i].strip() != "":
      if lines[i].startswith("data:"):
        data_lines.append(lines[i][len("data:"):].lstrip(" "))
      i += 1

    if data_lines:
      json_str = "\n".join(data_lines).strip()
      try:
        candidates.append(json.loads(json_str))
      except Exception:
        pass

    i += 1

  if not candidates: return None
  return candidates[-1] if last else candidates[0]


def _safe_json_dumps(data: Any) -> str:
  return json.dumps(data, ensure_ascii=False)


def _format_sse_event(event_name: str, message: str) -> str:
  if message is None: message = ""
  lines = str(message).splitlines() or [""]
  data_lines = "\n".join([f"data: {line}" for line in lines])
  return f"event: {event_name}\n{data_lines}\n\n"


def _sanitize_filename_component(value: Optional[str]) -> Optional[str]:
  if value is None: return None
  v = str(value).replace("\\", "_").replace("/", "_")
  v = v.replace("[", "").replace("]", "")
  v = v.replace(":", "_").replace("*", "_").replace("?", "_").replace('"', "_")
  v = v.replace("<", "_").replace(">", "_").replace("|", "_")
  return v


def _rename_file_if_exists(from_path: str, to_path: str) -> bool:
  if not os.path.exists(from_path): return False
  os.rename(from_path, to_path)
  return True


def _extract_router_from_path(jobs_root: str, file_path: str) -> str:
  rel = os.path.relpath(os.path.dirname(file_path), jobs_root)
  if rel == ".": return ""
  return rel.split(os.sep)[0]


class StreamingJobWriter:

  def __init__(
    self,
    persistent_storage_path: str,
    router_name: str,
    action: str,
    object_id: Optional[str],
    source_url: str,
    router_prefix: str,
    buffer_size: int = CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_LOG_EVENTS_PER_WRITE,
  ):
    self.persistent_storage_path = persistent_storage_path
    self.router_name = (router_name or "").strip("/")
    self.action = _sanitize_filename_component(action) or "action"
    self.object_id = _sanitize_filename_component(object_id)
    self.source_url = source_url or ""
    self.router_prefix = router_prefix or ""
    self.buffer_size = max(1, int(buffer_size or 1))

    self._jobs_root = _get_jobs_root(persistent_storage_path)

    folder_parts = [p for p in self.router_name.split("/") if p]
    self._router_folder = os.path.join(self._jobs_root, *folder_parts) if folder_parts else self._jobs_root
    os.makedirs(self._router_folder, exist_ok=True)

    self._buffer: list[str] = []
    self._current_state_ext: JobState = "running"
    self._end_emitted = False
    self._final_state_ext: Optional[JobState] = None

    self._timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    self._started_utc = _utc_now_iso()
    self._finished_utc: Optional[str] = None

    self._job_id, self._file_base = self._create_job_file_base_with_retry(max_retries=5)
    self._job_file_path = f"{self._file_base}.running"

  @property
  def job_id(self) -> str:
    return self._job_id

  @property
  def monitor_url(self) -> str:
    return f"{self.router_prefix}/jobs/monitor?job_id={self.job_id}&format=stream"

  def _create_job_file_base_with_retry(self, max_retries: int = 3) -> tuple[str, str]:
    for _ in range(max_retries):
      job_id = generate_job_id(self.persistent_storage_path)
      object_part = f"_[{self.object_id}]" if self.object_id else ""
      base_name = f"{self._timestamp}_[{self.action}]_[{job_id}]{object_part}"
      base_path = os.path.join(self._router_folder, base_name)
      try:
        with open(f"{base_path}.running", "x", encoding="utf-8"):
          pass
        return job_id, base_path
      except FileExistsError:
        continue

    raise RuntimeError("Failed to create streaming job file after retries")

  def _flush_buffer(self) -> None:
    if not self._buffer: return
    with open(f"{self._file_base}.{self._current_state_ext}", "a", encoding="utf-8") as f:
      f.write("".join(self._buffer))
      f.flush()
    self._buffer = []

  def _append_to_file_immediately(self, sse_chunk: str) -> None:
    self._flush_buffer()
    with open(f"{self._file_base}.{self._current_state_ext}", "a", encoding="utf-8") as f:
      f.write(sse_chunk)
      f.flush()

  def _transition_state(self, new_state: JobState) -> None:
    if new_state == self._current_state_ext: return
    from_path = f"{self._file_base}.{self._current_state_ext}"
    to_path = f"{self._file_base}.{new_state}"
    if _rename_file_if_exists(from_path, to_path):
      self._current_state_ext = new_state

  def emit_start(self) -> str:
    start_data = {
      "job_id": self.job_id,
      "state": "running",
      "source_url": self.source_url,
      "monitor_url": self.monitor_url,
      "started_utc": self._started_utc,
      "finished_utc": None,
      "result": None,
    }
    sse = _format_sse_event("start_json", _safe_json_dumps(start_data))
    self._append_to_file_immediately(sse)
    return sse

  def emit_log(self, message: str, flush: bool = False) -> str:
    sse = _format_sse_event("log", message)
    self._buffer.append(sse)
    if flush or len(self._buffer) >= self.buffer_size:
      self._flush_buffer()
    return sse

  def emit_log_with_standard_logging(self, log_data, message: str) -> str:
    from utils import log_function_output

    log_function_output(log_data, message)
    return self.emit_log(message)

  def emit_end(self, ok: bool, error: str = "", data: dict | None = None) -> str:
    self._flush_buffer()

    self._finished_utc = _utc_now_iso()

    is_cancelled = ("cancel" in (error or "").lower())
    state: JobState = "cancelled" if (not ok and is_cancelled) else "completed"

    end_data = {
      "job_id": self.job_id,
      "state": state,
      "source_url": self.source_url,
      "monitor_url": self.monitor_url,
      "started_utc": self._started_utc,
      "finished_utc": self._finished_utc,
      "result": {"ok": bool(ok), "error": error or "", "data": data or {}},
    }

    sse = _format_sse_event("end_json", _safe_json_dumps(end_data))
    self._append_to_file_immediately(sse)
    self._end_emitted = True
    self._final_state_ext = state
    return sse

  async def check_control(self) -> tuple[list[str], Optional[ControlAction]]:
    self._flush_buffer()

    cancel_path = f"{self._file_base}.cancel_requested"
    pause_path = f"{self._file_base}.pause_requested"
    resume_path = f"{self._file_base}.resume_requested"

    if os.path.exists(cancel_path):
      try: os.unlink(cancel_path)
      except Exception: pass
      return [], ControlAction.CANCEL

    if os.path.exists(pause_path) and self._current_state_ext == "running":
      try: os.unlink(pause_path)
      except Exception: pass
      pause_log = self.emit_log("  Pause requested, pausing...", flush=True)
      self._transition_state("paused")

      while True:
        await asyncio.sleep(0.1)

        if os.path.exists(cancel_path):
          try: os.unlink(cancel_path)
          except Exception: pass
          cancel_log = self.emit_log("  Cancel requested while paused, stopping...", flush=True)
          return [pause_log, cancel_log], ControlAction.CANCEL

        if os.path.exists(resume_path):
          try: os.unlink(resume_path)
          except Exception: pass
          resume_log = self.emit_log("  Resume requested, resuming...", flush=True)
          self._transition_state("running")
          return [pause_log, resume_log], None

    return [], None

  def finalize(self) -> None:
    self._flush_buffer()
    if self._end_emitted and self._final_state_ext:
      self._transition_state(self._final_state_ext)


def find_job_by_id(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  if not job_id: return None
  jobs_root = _get_jobs_root(persistent_storage_path)

  for file_path in _iter_job_state_files(persistent_storage_path):
    name = os.path.basename(file_path)
    if f"[{job_id}]" not in name: continue

    _, ext = os.path.splitext(name)
    state = ext.lstrip(".")
    if state not in VALID_JOB_STATES: continue

    try:
      with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    except Exception:
      continue

    start_json = _parse_sse_event_json(content, "start_json") or {}
    end_json = _parse_sse_event_json(content, "end_json", last=True) or {}

    source_url = str(start_json.get("source_url", ""))
    monitor_url = str(start_json.get("monitor_url", ""))
    started_utc = str(start_json.get("started_utc", ""))
    finished_utc = end_json.get("finished_utc", None)
    result = end_json.get("result", None)

    return JobMetadata(
      job_id=job_id,
      state=state,  # type: ignore[arg-type]
      source_url=source_url,
      monitor_url=monitor_url,
      started_utc=started_utc,
      finished_utc=finished_utc,
      result=result,
    )

  return None


def get_job_metadata(persistent_storage_path: str, job_id: str) -> Optional[JobMetadata]:
  return find_job_by_id(persistent_storage_path, job_id)


def list_jobs(persistent_storage_path: str, router_filter: str | None = None, state_filter: str | None = None) -> list[JobMetadata]:
  jobs_root = _get_jobs_root(persistent_storage_path)

  entries = []
  for file_path in _iter_job_state_files(persistent_storage_path):
    name = os.path.basename(file_path)
    _, ext = os.path.splitext(name)
    state = ext.lstrip(".")

    if state_filter and state != state_filter: continue
    if router_filter:
      router_name = _extract_router_from_path(jobs_root, file_path)
      if router_name != router_filter: continue

    job_number = _extract_job_number_from_filename(name)
    if job_number is None: continue
    job_id = f"jb_{job_number}"

    meta = find_job_by_id(persistent_storage_path, job_id)
    if meta is None:
      meta = JobMetadata(job_id=job_id, state=state, source_url="", monitor_url="", started_utc="", finished_utc=None, result=None)  # type: ignore[arg-type]

    entries.append((os.path.getmtime(file_path), meta))

  entries.sort(key=lambda x: x[0], reverse=True)
  return [m for _, m in entries]


def read_job_log(persistent_storage_path: str, job_id: str) -> str:
  meta = find_job_by_id(persistent_storage_path, job_id)
  if not meta: return ""

  jobs_root = _get_jobs_root(persistent_storage_path)
  for file_path in _iter_job_state_files(persistent_storage_path):
    if f"[{job_id}]" in os.path.basename(file_path):
      try:
        with open(file_path, "r", encoding="utf-8") as f:
          return f.read()
      except Exception:
        return ""

  return ""


def read_job_result(persistent_storage_path: str, job_id: str) -> Optional[dict]:
  meta = find_job_by_id(persistent_storage_path, job_id)
  if not meta: return None
  if meta.state not in ("completed", "cancelled"): return None
  return meta.result


def create_control_file(persistent_storage_path: str, job_id: str, action: str) -> bool:
  if action not in ("pause", "resume", "cancel"): return False
  meta = find_job_by_id(persistent_storage_path, job_id)
  if not meta: return False

  jobs_root = _get_jobs_root(persistent_storage_path)
  for file_path in _iter_job_state_files(persistent_storage_path):
    if f"[{job_id}]" not in os.path.basename(file_path): continue

    file_base = os.path.splitext(file_path)[0]
    control_path = f"{file_base}.{action}_requested"
    try:
      with open(control_path, "w", encoding="utf-8") as f:
        f.write("")
      return True
    except Exception:
      return False

  return False


def delete_job(persistent_storage_path: str, job_id: str) -> bool:
  for file_path in _iter_job_state_files(persistent_storage_path):
    if f"[{job_id}]" in os.path.basename(file_path):
      try:
        os.unlink(file_path)
        return True
      except Exception:
        return False
  return False
