from typing import Dict, Any, List
import datetime
import os
import html
import logging
import sys

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

# Format a file size in bytes into a human-readable string
def format_filesize(num_bytes):
  if not num_bytes: return ''
  for unit in ['B','KB','MB','GB','TB']:
    if num_bytes < 1024: return f"{num_bytes:.2f} {unit}"
    num_bytes /= 1024
  return f"{num_bytes:.2f} PB"

# Format timestamp into a human-readable string (RFC3339 with ' ' instead of 'T')
def format_timestamp(ts):
  return ('' if not ts else datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))

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

def log_function_header(function_name: str) -> Dict[str, Any]:
  global _request_counter
  _request_counter += 1
  process_id = os.getpid()
  start_time = datetime.datetime.now()
  data: Dict[str, Any] = {"function_name": function_name, "start_time": start_time, "request_number": _request_counter}
  logger.info(f"[{start_time.strftime('%Y-%m-%d %H:%M:%S')},process {process_id},request {_request_counter},{function_name}] START: {function_name}...")
  return data

async def log_function_footer(log_data: Dict[str, Any]) -> None:
  function_name, start_time, request_number = log_data["function_name"], log_data["start_time"], log_data["request_number"]
  process_id = os.getpid()
  end_time = datetime.datetime.now()
  ms = int((end_time - start_time).total_seconds() * 1000)
  total_time = format_milliseconds(ms)
  logger.info(f"[{end_time.strftime('%Y-%m-%d %H:%M:%S')},process {process_id},request {request_number},{function_name}] END: {function_name} ({total_time}).")

def log_function_output(log_data: Dict[str, Any], output):
  function_name, request_number = log_data["function_name"], log_data["request_number"]
  process_id = os.getpid()
  timestamp = datetime.datetime.now()
  logger.info(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')},process {process_id},request {request_number},{function_name}] {output}")

def truncate_string(string, max_length, append="…"):
  if len(string) > max_length:
    return string[:max_length] + append
  return string

def clean_response(string):
  if len(string) > 0: return string.replace("\n", "").replace("\r", "").replace("'","").replace('"',"").strip()
  return string

def remove_linebreaks(string):
  if len(string) > 0: return string.replace("\n", " ").replace("\r", " ").strip()
  return string

def sanitize_queries_and_responses(string):
  remove_marker = "***[REMOVED]***"
  string_max_visible_chars = 5
  if not log_queries_and_responses and len(string) > string_max_visible_chars : return truncate_string(string, string_max_visible_chars,"") + remove_marker
  return string

# Returns a nested html table from the given data (Dict or List or Array)
def convert_to_nested_html_table(data: Any, max_depth: int = 10) -> str:
  def handle_value(v: Any, depth: int) -> str:
    if depth >= max_depth: return html.escape(str(v))
    if isinstance(v, dict): return handle_dict(v, depth + 1)
    elif isinstance(v, list): return handle_list(v, depth + 1)
    else: return html.escape(str(v))

  def handle_list(items: List[Any], depth: int) -> str:
    if not items or depth >= max_depth: return html.escape(str(items))
    # For simple lists, just return the string representation
    if not any(isinstance(item, (dict, list)) for item in items): return html.escape(str(items))
    # For complex lists, create a table
    rows = [f"<tr><td>[{i}]</td><td>{handle_value(item, depth)}</td></tr>" for i, item in enumerate(items)]
    return f"<table border=1>{''.join(rows)}</table>"
  
  def handle_dict(d: Dict[str, Any], depth: int) -> str:
    if not d or depth >= max_depth: return html.escape(str(d))
    # Generic multi-column rendering when values are dict-like with shared keys
    dict_values = [v for v in d.values() if isinstance(v, dict)]
    if dict_values:
      # Find common keys across all dict values
      common_keys = set(dict_values[0].keys())
      for dict_val in dict_values[1:]:
        common_keys &= set(dict_val.keys())
      if common_keys:
        # Use keys in order they appear in first dict
        ordered_keys = [k for k in dict_values[0].keys() if k in common_keys]
        rows: List[str] = []
        for k, v in d.items():
          cells: List[str] = [html.escape(str(k))]
          if isinstance(v, dict):
            for subk in ordered_keys:
              cells.append(html.escape(str(v.get(subk, ""))))
          else:
            # Non-dict value: put entire value into first sub-column, leave others blank
            cells.append(html.escape(str(v)))
            for _ in range(len(ordered_keys) - 1): cells.append("")
          rows.append("<tr>" + "".join([f"<td>{c}</td>" for c in cells]) + "</tr>")
        header_cells = ["Key"] + [html.escape(str(k)) for k in ordered_keys]
        header = "<tr>" + "".join([f"<th>{h}</th>" for h in header_cells]) + "</tr>"
        return f"<table border=1>{header}{''.join(rows)}</table>"
    # Default: simple 2-column key/value rendering
    rows = [f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>" for k, v in d.items()]
    return f"<table border=1>{''.join(rows)}</table>"
  return handle_value(data, 1)
