import dataclasses, datetime, glob, html, logging, os, shutil, sys, tempfile, time, zipfile
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from routers_v1.common_logging_functions_v1 import log_function_output

def include_exclude_attributes(data: Union[List[Dict], Dict, List[Any], Any], include_attributes: Optional[str] = None, exclude_attributes: Optional[str] = None) -> Union[List[Dict], Dict]:
  """
  Filter attributes in data objects based on include/exclude parameters.
  Supports dicts, dataclasses, and lists of either.
  
  Args:
    data: Single dict/dataclass or list of dicts/dataclasses to filter
    include_attributes: Comma-separated list of attributes to include (takes precedence)
    exclude_attributes: Comma-separated list of attributes to exclude (ignored if include_attributes is set)
    
  Returns:
    Filtered data with only specified attributes (always returns dicts, not dataclasses)
  """
  if not include_attributes and not exclude_attributes: 
    # Convert dataclasses to dicts if no filtering
    if is_dataclass(data) and not isinstance(data, type):
      return asdict(data)
    if isinstance(data, list) and len(data) > 0 and is_dataclass(data[0]) and not isinstance(data[0], type):
      return [asdict(item) for item in data]
    return data
  
  # Handle single object (dict or dataclass)
  if is_dataclass(data) and not isinstance(data, type):
    return _filter_single_object(asdict(data), include_attributes, exclude_attributes)
  if isinstance(data, dict):
    return _filter_single_object(data, include_attributes, exclude_attributes)
  
  # Handle list of objects
  if isinstance(data, list):
    result = []
    for item in data:
      if is_dataclass(item) and not isinstance(item, type):
        result.append(_filter_single_object(asdict(item), include_attributes, exclude_attributes))
      elif isinstance(item, dict):
        result.append(_filter_single_object(item, include_attributes, exclude_attributes))
      else:
        result.append(item)
    return result
  
  return data

def _filter_single_object(obj: Dict, include_attributes: Optional[str], exclude_attributes: Optional[str]) -> Dict:
  """
  Filter a single object based on include/exclude attributes. If includes are given, excludes are ignored.
  """
  if not isinstance(obj, dict): 
    return obj
  
  # If include_attributes is specified, only include those attributes
  if include_attributes:
    include_list = [attr.strip() for attr in include_attributes.split(',') if attr.strip()]
    return {key: value for key, value in obj.items() if key in include_list}
  
  # If exclude_attributes is specified, exclude those attributes
  if exclude_attributes:
    exclude_list = [attr.strip() for attr in exclude_attributes.split(',') if attr.strip()]
    return {key: value for key, value in obj.items() if key not in exclude_list}
  
  return obj

class ZipExtractionMode(Enum):
  DO_NOT_OVERWRITE = "do_not_overwrite"
  OVERWRITE_IF_NEWER = "overwrite_if_newer"
  OVERWRITE = "overwrite"


@contextmanager
def acquire_startup_lock(lock_name: str, log_data: Dict[str, Any], timeout_seconds: int = 30):
  """Acquire a file-based lock to ensure only one worker performs startup tasks.
  
  Uses a lock file mechanism that works across processes. The first worker to acquire
  the lock will execute the protected code block. Other workers will wait until the
  lock is released or timeout occurs.
  
  Args:
    lock_name: Name of the lock (used to create lock file)
    log_data: Logging context from log_function_header
    timeout_seconds: Maximum time to wait for lock acquisition
    
  Yields:
    bool: True if lock was acquired (worker should proceed), False if another worker already completed the task
  """
  lock_file_path = os.path.join(tempfile.gettempdir(), f"{lock_name}.lock")
  done_file_path = os.path.join(tempfile.gettempdir(), f"{lock_name}.done")
  lock_fd = None
  acquired = False
  
  try:
    # Check if task was already completed by another worker
    if os.path.exists(done_file_path):
      log_function_output(log_data, f"Startup lock task '{lock_name}': already completed by another worker, skipping (done file exists: '{done_file_path}')")
      yield False
      return
    
    # Try to acquire lock with timeout
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
      try:
        # Try to create lock file exclusively (fails if exists)
        lock_fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        acquired = True
        log_function_output(log_data, f"Startup lock task '{lock_name}': Created lock file '{lock_file_path}' (PID: {os.getpid()})")
        
        # Check again if task was completed while we were waiting
        if os.path.exists(done_file_path):
          log_function_output(log_data, f"Startup lock task '{lock_name}': completed while acquiring lock, skipping")
          yield False
          return
        
        # Lock acquired, proceed with task
        yield True
        
        # Mark task as done
        try:
          with open(done_file_path, 'w') as f:
            f.write(f"{os.getpid()}\n{time.time()}\n")
          log_function_output(log_data, f"Startup lock task '{lock_name}': marked as completed (created done file: '{done_file_path}')")
        except Exception as e:
          log_function_output(log_data, f"Startup lock task '{lock_name}': WARNING - Failed to create done file at '{done_file_path}': {e}")
        
        return
        
      except FileExistsError:
        # Lock file exists, another worker has the lock
        time.sleep(0.1)
        
        # Check if done file appeared while waiting
        if os.path.exists(done_file_path):
          log_function_output(log_data, f"Startup lock task '{lock_name}': completed by another worker while waiting (done file exists: '{done_file_path}')")
          yield False
          return
      except Exception as e:
        log_function_output(log_data, f"Startup lock task '{lock_name}': WARNING - Error acquiring lock: {e}")
        break
    
    # Timeout occurred
    log_function_output(log_data, f"Startup lock task '{lock_name}': WARNING - Timeout waiting for lock, checking if task is done")
    if os.path.exists(done_file_path):
      log_function_output(log_data, f"Startup lock task '{lock_name}': was completed, skipping (done file exists: '{done_file_path}')")
      yield False
    else:
      log_function_output(log_data, f"Startup lock task '{lock_name}': WARNING - Timeout and task not done, proceeding anyway (may cause race condition)")
      yield True
    
  finally:
    # Release lock
    if acquired and lock_fd is not None:
      try:
        os.close(lock_fd)
        os.unlink(lock_file_path)
        log_function_output(log_data, f"Startup lock task '{lock_name}': Deleted lock file '{lock_file_path}'")
      except Exception as e:
        log_function_output(log_data, f"Startup lock task '{lock_name}': WARNING - Error deleting lock file '{lock_file_path}': {e}")


def clear_folder(folder_path: str, include_subfolders: bool, log_data: Dict[str, Any]) -> None:
  """Clear all files and optionally subfolders from the specified folder.
  
  Args:
    folder_path: Path to the folder to clear
    include_subfolders: If True, removes subfolders as well; if False, only removes files
  """
  if not os.path.exists(folder_path):
    log_function_output(log_data, f"Folder does not exist: {folder_path}")
    return
  
  if not os.path.isdir(folder_path):
    log_function_output(log_data, f"Path is not a directory: {folder_path}")
    return
  
  try:
    for item in os.listdir(folder_path):
      item_path = os.path.join(folder_path, item)
      
      if os.path.isfile(item_path):
        os.remove(item_path)
        log_function_output(log_data, f"Removed file: {item_path}")
      elif os.path.isdir(item_path) and include_subfolders:
        shutil.rmtree(item_path)
        log_function_output(log_data, f"Removed folder: {item_path}")
    
    log_function_output(log_data, f"Successfully cleared folder: {folder_path}")
  except Exception as e:
    log_function_output(log_data, f"Error clearing folder {folder_path}: {str(e)}")
    raise

def extract_zip_files(source_folder: str, destination_folder: str, mode: ZipExtractionMode, initialization_errors: List[Dict[str, str]]) -> List[str]:
  """Extract all zip files from source folder to destination folder based on the specified mode.
  
  Returns:
      List[str]: List of absolute paths of all extracted files.
  """
  extracted_files = []
  try:
    if not os.path.exists(source_folder):
      return extracted_files
    
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
            
            # Extract if neededI asdf
            if should_extract:
              os.makedirs(target_dir_path, exist_ok=True)
              with zip_ref.open(member) as source, open(target_file_path, 'wb') as target:
                shutil.copyfileobj(source, target)
              
              # Set file timestamp to match zip entry
              zip_file_time = member.date_time
              zip_timestamp = time.mktime(zip_file_time + (0, 0, -1))
              os.utime(target_file_path, (zip_timestamp, zip_timestamp))
              
              # Add to list of extracted files
              extracted_files.append(os.path.abspath(target_file_path))
          
          print(f"Extracted {zip_file_path} to {destination_folder} ({mode.value} mode)")
        
      except Exception as e:
        initialization_errors.append({"component": f"Zip Extraction ({mode.value})", "error": f"Failed to extract {zip_file_path}: {str(e)}"})
  except Exception as e:
    initialization_errors.append({"component": f"Zip Extraction ({mode.value})", "error": str(e)})
  
  return extracted_files


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


def normalize_long_path(path: str) -> str:
  """
  Normalize a path to handle Windows long path limitations (>260 characters).
  
  On Windows, paths longer than 260 characters require special prefixes:
  - Regular paths: \\\\?\\ prefix
  - UNC paths: \\\\?\\UNC\\ prefix
  
  Args:
    path: The path to normalize
    
  Returns:
    Normalized path with long path prefix if needed on Windows
  """
  if os.name == 'nt' and not path.startswith('\\\\?\\'):
    abs_path = os.path.abspath(path)
    if len(abs_path) > 260:
      if abs_path.startswith('\\\\'):
        return '\\\\?\\UNC\\' + abs_path[2:]
      else:
        return '\\\\?\\' + abs_path
  return path


def clean_response(string):
  if len(string) > 0: return string.replace("\n", "").replace("\r", "").replace("'","").replace('"',"").strip()
  return string

def remove_linebreaks(string):
  if len(string) > 0: return string.replace("\n", " ").replace("\r", " ").strip()
  return string


# Returns a nested html table from the given data (Dict, List, Array, DataClass)
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
def convert_to_flat_html_table(data: Any) -> str:
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

