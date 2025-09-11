import dataclasses, datetime, glob, html, logging, os, shutil, sys, time, zipfile
from enum import Enum
from typing import Any, Dict, List

# Configure logging for multi-worker environment
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ZipExtractionMode(Enum):
  DO_NOT_OVERWRITE = "do_not_overwrite"
  OVERWRITE_IF_NEWER = "overwrite_if_newer"
  OVERWRITE = "overwrite"

def extract_zip_files(source_folder: str, destination_folder: str, mode: ZipExtractionMode, initialization_errors: List[Dict[str, str]]) -> None:
  """Extract all zip files from source folder to destination folder based on the specified mode."""
  try:
    if not os.path.exists(source_folder):
      return
    
    zip_files = glob.glob(os.path.join(source_folder, "*.zip"))
    for zip_file_path in zip_files:
      try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
          # Process all files in zip
          for member in zip_ref.infolist():
            target_file_path = os.path.join(destination_folder, member.filename)
            target_dir_path = os.path.dirname(target_file_path)
            
            # Handle directories
            if member.is_dir():
              os.makedirs(target_dir_path, exist_ok=True)
              continue
            
            # Determine if we should extract based on mode
            should_extract = False
            if mode == ZipExtractionMode.OVERWRITE:
              should_extract = True
            elif mode == ZipExtractionMode.DO_NOT_OVERWRITE:
              should_extract = not os.path.exists(target_file_path)
            elif mode == ZipExtractionMode.OVERWRITE_IF_NEWER:
              if not os.path.exists(target_file_path):
                should_extract = True
              else:
                # Get modification times
                zip_file_time = member.date_time
                target_file_mtime = os.path.getmtime(target_file_path)
                zip_timestamp = time.mktime(zip_file_time + (0, 0, -1))
                
                # Check directory timestamp first
                if os.path.exists(target_dir_path):
                  dir_mtime = os.path.getmtime(target_dir_path)
                  should_extract = dir_mtime < zip_timestamp or target_file_mtime <= zip_timestamp
                else:
                  should_extract = True
            else:
              should_extract = True
            
            # Extract if needed
            if should_extract:
              os.makedirs(target_dir_path, exist_ok=True)
              with zip_ref.open(member) as source, open(target_file_path, 'wb') as target:
                shutil.copyfileobj(source, target)
              
              # Set file timestamp to match zip entry
              zip_file_time = member.date_time
              zip_timestamp = time.mktime(zip_file_time + (0, 0, -1))
              os.utime(target_file_path, (zip_timestamp, zip_timestamp))
          
          print(f"Extracted {zip_file_path} to {destination_folder} ({mode.value} mode)")
        
      except Exception as e:
        initialization_errors.append({"component": f"Zip Extraction ({mode.value})", "error": f"Failed to extract {zip_file_path}: {str(e)}"})
  except Exception as e:
    initialization_errors.append({"component": f"Zip Extraction ({mode.value})", "error": str(e)})

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

# Format configuration dataclass for display (mask secrets, handle None values)
def format_config_for_displaying(config_obj) -> Dict[str, Any]:
  result = {}
  for field in dataclasses.fields(config_obj):
    value = getattr(config_obj, field.name)    
    if field.name.endswith("_KEY") or field.name.endswith("_SECRET"): result[field.name] = "✅ [CONFIGURED]" if value else "⚠️ [NOT CONFIGURED]"
    elif value is None: result[field.name] = "⚠️ [NOT CONFIGURED]"
    else: result[field.name] = "✅ " + str(value)
  return result

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
    elif dataclasses.is_dataclass(v): return handle_dataclass(v, depth + 1)
    else: return html.escape(str(v))
  
  def handle_dataclass(dc: Any, depth: int) -> str:
    if depth >= max_depth: return html.escape(str(dc))
    # Convert dataclass to dict for consistent handling
    dc_dict = {field.name: getattr(dc, field.name) for field in dataclasses.fields(dc)}
    return handle_dict(dc_dict, depth)


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
    rows = [f"<tr><td>{html.escape(str(k))}</td><td>{handle_value(v, depth)}</td></tr>" for k, v in d.items()]
    return f"<table border=1>{''.join(rows)}</table>"
  return handle_value(data, 1)

# Returns a formatted HTML table from lists, dicts, or arrays with proper rows and columns
def convert_to_html_table(data: Any) -> str:
  if not data: return "<p>No data</p>"
  
  # Handle list of dictionaries (like initialization_errors)
  if isinstance(data, list):
    if not data: return "<p>No items</p>"
    
    # Check if all items are dictionaries with same keys
    if all(isinstance(item, dict) for item in data):
      # Get all unique keys from all dictionaries, preserving order
      all_keys = []
      seen_keys = set()
      for item in data:
        for key in item.keys():
          if key not in seen_keys:
            all_keys.append(key)
            seen_keys.add(key)
      
      if all_keys:
        # Create table with headers
        header_row = "".join(f"<th>{html.escape(str(key))}</th>" for key in all_keys)
        rows = []
        for item in data:
          cells = []
          for key in all_keys:
            value = item.get(key, "")
            cells.append(f"<td>{html.escape(str(value))}</td>")
          rows.append(f"<tr>{''.join(cells)}</tr>")
        return f"<table border=1><tr>{header_row}</tr>{''.join(rows)}</table>"
    
    # Handle simple list or mixed content
    rows = [f"<tr><td>[{i}]</td><td>{html.escape(str(item))}</td></tr>" for i, item in enumerate(data)]
    return f"<table border=1><tr><th>Index</th><th>Value</th></tr>{''.join(rows)}</table>"
  
  # Handle dictionary (like results or config)
  elif isinstance(data, dict):
    if not data: return "<p>No data</p>"
    
    # Check if values are dictionaries with consistent structure (like results)
    values_are_dicts = all(isinstance(v, dict) for v in data.values())
    if values_are_dicts and data:
      # Get all unique keys from all value dictionaries, preserving order
      all_value_keys = []
      seen_keys = set()
      for v in data.values():
        if isinstance(v, dict):
          for key in v.keys():
            if key not in seen_keys:
              all_value_keys.append(key)
              seen_keys.add(key)
      
      if all_value_keys:
        # Create table with main key + sub-keys as columns
        header_row = f"<th>Key</th>{''.join(f'<th>{html.escape(str(key))}</th>' for key in all_value_keys)}"
        rows = []
        for main_key, value_dict in data.items():
          cells = [f"<td>{html.escape(str(main_key))}</td>"]
          for sub_key in all_value_keys:
            sub_value = value_dict.get(sub_key, "") if isinstance(value_dict, dict) else ""
            cells.append(f"<td>{html.escape(str(sub_value))}</td>")
          rows.append(f"<tr>{''.join(cells)}</tr>")
        return f"<table border=1><tr>{header_row}</tr>{''.join(rows)}</table>"
    
    # Handle simple key-value dictionary
    rows = [f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>" for k, v in data.items()]
    return f"<table border=1><tr><th>Key</th><th>Value</th></tr>{''.join(rows)}</table>"
  
  # Handle other types
  else:
    return f"<table border=1><tr><th>Value</th></tr><tr><td>{html.escape(str(data))}</td></tr></table>"