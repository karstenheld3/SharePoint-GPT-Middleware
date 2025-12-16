import datetime, logging, os, sys
from typing import Any, Dict

# Configure logging for multi-worker environment
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global request counter
_request_counter = 0

# Feature flag for logging queries and responses
log_queries_and_responses = os.getenv("LOG_QUERIES_AND_RESPONSES", "false").lower() == "true"

def log_function_header(function_name: str) -> Dict[str, Any]:
  global _request_counter
  _request_counter += 1
  process_id = os.getpid()
  start_time = datetime.datetime.now()
  data: Dict[str, Any] = {"function_name": function_name, "start_time": start_time, "request_number": _request_counter}
  logger.info(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')},process {process_id},request {_request_counter},{function_name}] START: {function_name}...")
  return data

def _log_function_footer_impl(log_data: Dict[str, Any]) -> None:
  """Internal helper to implement footer logging logic."""
  function_name, start_time, request_number = log_data["function_name"], log_data["start_time"], log_data["request_number"]
  process_id = os.getpid()
  end_time = datetime.datetime.now()
  ms = int((end_time - start_time).total_seconds() * 1000)
  total_time = format_milliseconds(ms)
  logger.info(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')},process {process_id},request {request_number},{function_name}] END: {function_name} ({total_time}).")

async def log_function_footer(log_data: Dict[str, Any]) -> None:
  """Async version of function footer logging."""
  _log_function_footer_impl(log_data)

def log_function_footer_sync(log_data: Dict[str, Any]) -> None:
  """Sync version of function footer logging."""
  _log_function_footer_impl(log_data)

def log_function_output(log_data: Dict[str, Any], output):
  function_name, request_number = log_data["function_name"], log_data["request_number"]
  process_id = os.getpid()
  timestamp = datetime.datetime.now()
  logger.info(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')},process {process_id},request {request_number},{function_name}] {output}")

def truncate_string(string, max_length, append="…"):
  if len(string) > max_length:
    return string[:max_length] + append
  return string

def sanitize_queries_and_responses(string):
  remove_marker = "***[REMOVED]***"
  string_max_visible_chars = 5
  if not log_queries_and_responses and len(string) > string_max_visible_chars : return truncate_string(string, string_max_visible_chars,"") + remove_marker
  return string

# Format milliseconds into a human-readable string
def format_milliseconds(millisecs: int) -> str:
  if millisecs < 1000: return f"{millisecs} ms"
  # For durations under 50 seconds, show one decimal for seconds
  if millisecs < 50000:
    seconds_float = round(millisecs / 1000.0, 1)
    unit = "sec" if seconds_float == 1.0 else "secs"
    return f"{seconds_float:.1f} {unit}"
  secs = millisecs // 1000; hours = secs // 3600; minutes = (secs % 3600) // 60; seconds = secs % 60
  parts = []
  if hours: parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
  if minutes: parts.append(f"{minutes} min{'s' if minutes != 1 else ''}")
  if seconds: parts.append(f"{seconds} sec{'s' if seconds != 1 else ''}")
  return ', '.join(parts) if parts else "0 sec"
