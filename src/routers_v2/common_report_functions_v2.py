# Common Report Functions V2
# Target file: /src/routers_v2/common_report_functions_v2.py
# Spec: _V2_SPEC_REPORTS.md

import zipfile, json, datetime, os, sys
from pathlib import Path
from typing import Optional
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN

# Module-level config - set via set_config()
config = None

# Long path support for Windows (>260 chars)
def _long_path(path: Path) -> Path:
  if sys.platform == 'win32':
    s = str(path.resolve())
    if len(s) > 240 and not s.startswith('\\\\?\\'):
      return Path('\\\\?\\' + s)
  return path

def set_config(app_config):
  global config
  config = app_config

def get_reports_path() -> Path:
  storage_path = getattr(config, 'LOCAL_PERSISTENT_STORAGE_PATH', None) or ''
  return Path(storage_path) / "reports"

# ----------------------------------------- START: Type/Folder Conversion -----------------------------------------------------

def get_folder_for_type(report_type: str) -> str:
  if report_type == "site_scan": return "site_scans"
  return report_type + "s"

def get_type_from_folder(folder: str) -> str:
  if folder == "site_scans": return "site_scan"
  return folder.rstrip("s")

# ----------------------------------------- END: Type/Folder Conversion -------------------------------------------------------


# ----------------------------------------- START: Report CRUD Functions ------------------------------------------------------

def create_report(report_type: str, filename: str, files: list[tuple[str, bytes]], metadata: dict, keep_folder_structure: bool = True, dry_run: bool = False, logger: Optional[MiddlewareLogger] = None) -> str:
  """
  Create a report archive with report.json and provided files.
  Returns report_id on success.
  
  Args:
    report_type: "crawl", "site_scan", etc.
    filename: Archive filename without .zip extension
    files: List of (archive_path, content_bytes) tuples
    metadata: Dict with title, type, ok, error and type-specific fields
    keep_folder_structure: If True, preserve file paths; if False, flatten to root
    dry_run: If True, simulate without writing to disk
    logger: Optional MiddlewareLogger for logging
  """
  folder = get_folder_for_type(report_type)
  report_id = f"{folder}/{filename}"
  
  # Ensure folder exists
  reports_path = get_reports_path()
  folder_path = _long_path(reports_path / folder)
  folder_path.mkdir(parents=True, exist_ok=True)
  
  # Build archive path
  archive_path = _long_path(folder_path / f"{filename}.zip")
  
  if logger: logger.log_function_output(f"Creating report '{report_id}'...")
  
  # Add mandatory fields to metadata
  now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
  metadata["report_id"] = report_id
  metadata["created_utc"] = now_utc
  if "type" not in metadata: metadata["type"] = report_type
  
  # Build files inventory
  files_inventory = []
  for file_path, content in files:
    actual_path = file_path if keep_folder_structure else os.path.basename(file_path)
    files_inventory.append({
      "filename": os.path.basename(file_path),
      "file_path": actual_path,
      "file_size": len(content),
      "last_modified_utc": now_utc
    })
  
  # Add report.json to inventory
  report_json_content = json.dumps(metadata, indent=2, ensure_ascii=False).encode("utf-8")
  files_inventory.insert(0, {
    "filename": "report.json",
    "file_path": "report.json",
    "file_size": len(report_json_content),
    "last_modified_utc": now_utc
  })
  metadata["files"] = files_inventory
  
  # Re-serialize with files inventory included
  report_json_content = json.dumps(metadata, indent=2, ensure_ascii=False).encode("utf-8")
  # Update size after adding files array
  files_inventory[0]["file_size"] = len(report_json_content)
  report_json_content = json.dumps(metadata, indent=2, ensure_ascii=False).encode("utf-8")
  
  # Create zip archive
  if dry_run:
    if logger: logger.log_function_output(f"  DRY_RUN: Would create archive with {len(files) + 1} files.")
  else:
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
      zf.writestr("report.json", report_json_content)
      for file_path, content in files:
        actual_path = file_path if keep_folder_structure else os.path.basename(file_path)
        zf.writestr(actual_path, content)
    if logger: logger.log_function_output(f"  OK.")
  
  return report_id

def list_reports(type_filter: str = None, logger: Optional[MiddlewareLogger] = None) -> list[dict]:
  """
  List all reports, optionally filtered by type.
  Returns list of report.json contents, sorted by created_utc descending (newest first).
  """
  if logger: logger.log_function_output(f"Listing reports" + (f" (type='{type_filter}')" if type_filter else "") + "...")
  reports = []
  reports_path = _long_path(get_reports_path())
  
  if not reports_path.exists(): return []
  
  # Iterate through type folders
  for folder_path in reports_path.iterdir():
    if not folder_path.is_dir(): continue
    folder_name = folder_path.name
    folder_type = get_type_from_folder(folder_name)
    
    # Apply type filter
    if type_filter and folder_type != type_filter: continue
    
    # Iterate through zip files in folder
    for zip_path in folder_path.glob("*.zip"):
      try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
          if "report.json" not in zf.namelist():
            if logger: logger.log_function_output(f"  WARNING: Skipping '{zip_path}': missing report.json")
            continue
          report_json = json.loads(zf.read("report.json").decode("utf-8"))
          reports.append(report_json)
      except zipfile.BadZipFile:
        if logger: logger.log_function_output(f"  WARNING: Skipping corrupt zip: '{zip_path}'")
      except json.JSONDecodeError:
        if logger: logger.log_function_output(f"  WARNING: Skipping '{zip_path}': invalid JSON in report.json")
      except Exception as e:
        if logger: logger.log_function_output(f"  WARNING: Skipping '{zip_path}' -> {e}")
  
  # Sort by created_utc descending
  reports.sort(key=lambda r: r.get("created_utc", ""), reverse=True)
  if logger: logger.log_function_output(f"  {len(reports)} report{'' if len(reports) == 1 else 's'} found.")
  return reports

def get_report_metadata(report_id: str, logger: Optional[MiddlewareLogger] = None) -> dict | None:
  """
  Read and return report.json content from archive.
  Returns None if not found or invalid.
  """
  archive_path = get_report_archive_path(report_id)
  if archive_path is None: return None
  
  try:
    with zipfile.ZipFile(archive_path, 'r') as zf:
      if "report.json" not in zf.namelist(): return None
      return json.loads(zf.read("report.json").decode("utf-8"))
  except (zipfile.BadZipFile, json.JSONDecodeError, Exception) as e:
    if logger: logger.log_function_output(f"  WARNING: Failed to read report metadata for '{report_id}' -> {e}")
    return None

def get_report_file(report_id: str, file_path: str, logger: Optional[MiddlewareLogger] = None) -> bytes | None:
  """
  Read specific file from archive.
  Returns None if not found.
  """
  archive_path = get_report_archive_path(report_id)
  if archive_path is None: return None
  
  try:
    with zipfile.ZipFile(archive_path, 'r') as zf:
      if file_path not in zf.namelist(): return None
      return zf.read(file_path)
  except Exception as e:
    if logger: logger.log_function_output(f"  WARNING: Failed to read file '{file_path}' from report '{report_id}' -> {e}")
    return None

def delete_report(report_id: str, dry_run: bool = False, logger: Optional[MiddlewareLogger] = None) -> dict | None:
  """
  Delete archive file.
  Returns the deleted report metadata, or None if not found.
  """
  archive_path = get_report_archive_path(report_id)
  if archive_path is None: return None
  
  if logger: logger.log_function_output(f"Deleting report '{report_id}'...")
  
  # Read metadata before deleting
  metadata = get_report_metadata(report_id)
  
  if dry_run:
    if logger: logger.log_function_output(f"  DRY_RUN: Would delete archive.")
    return metadata
  
  try:
    archive_path.unlink()
    if logger: logger.log_function_output(f"  OK.")
    return metadata
  except Exception as e:
    if logger: logger.log_function_output(f"  ERROR: Failed to delete report '{report_id}' -> {e}")
    raise

def get_report_archive_path(report_id: str) -> Path | None:
  """
  Return full filesystem path to archive.
  Returns None if not found or invalid format.
  """
  if "/" not in report_id: return None
  
  folder, filename = report_id.split("/", 1)
  reports_path = get_reports_path()
  archive_path = _long_path(reports_path / folder / f"{filename}.zip")
  
  if not archive_path.exists(): return None
  return archive_path

# ----------------------------------------- END: Report CRUD Functions --------------------------------------------------------
