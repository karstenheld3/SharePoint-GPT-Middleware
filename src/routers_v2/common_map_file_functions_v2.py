# Map File Functions V2 - CSV map file I/O with buffered writes and change detection
# Implements MapFileWriter class and change detection per _V2_SPEC_CRAWLER.md specification

import csv, os, tempfile
from dataclasses import dataclass, fields, asdict
from typing import Optional

from hardcoded_config import CRAWLER_HARDCODED_CONFIG


# ----------------------------------------- START: Dataclasses --------------------------------------------------------

@dataclass
class SharePointMapRow:
  """Row in sharepoint_map.csv - current SharePoint state (10 fields)."""
  sharepoint_listitem_id: int
  sharepoint_unique_file_id: str
  filename: str
  file_type: str
  file_size: int
  url: str
  raw_url: str
  server_relative_url: str
  last_modified_utc: str
  last_modified_timestamp: int

@dataclass
class FilesMapRow:
  """Row in files_map.csv - local file state (13 fields)."""
  sharepoint_listitem_id: int
  sharepoint_unique_file_id: str
  filename: str
  file_type: str
  server_relative_url: str
  file_relative_path: str  # Empty if download failed
  file_size: int
  last_modified_utc: str
  last_modified_timestamp: int
  downloaded_utc: str
  downloaded_timestamp: int
  sharepoint_error: str
  processing_error: str

@dataclass
class VectorStoreMapRow:
  """Row in vectorstore_map.csv - embedded file state (19 fields)."""
  openai_file_id: str
  vector_store_id: str
  file_relative_path: str
  sharepoint_listitem_id: int
  sharepoint_unique_file_id: str
  filename: str
  file_type: str
  file_size: int
  last_modified_utc: str
  last_modified_timestamp: int
  downloaded_utc: str
  downloaded_timestamp: int
  uploaded_utc: str
  uploaded_timestamp: int
  embedded_utc: str
  embedded_timestamp: int
  sharepoint_error: str
  processing_error: str
  embedding_error: str

@dataclass
class ChangeDetectionResult:
  """Result of comparing SharePoint state vs local state (4 fields)."""
  added: list      # list[SharePointMapRow] - New files in SharePoint
  removed: list    # list[FilesMapRow] - Files no longer in SharePoint
  changed: list    # list[SharePointMapRow] - Files with field differences
  unchanged: list  # list[FilesMapRow] - Files matching exactly

# ----------------------------------------- END: Dataclasses ----------------------------------------------------------


# ----------------------------------------- START: MapFileWriter Class ------------------------------------------------

class MapFileWriter:
  """
  Buffered writer for CSV map files with graceful error handling.
  Implements V2CR-FR-05: Buffered append writes.
  
  Usage:
    writer = MapFileWriter(filepath, SharePointMapRow)
    writer.write_header()
    for item in items:
      writer.append_row(item)
    writer.finalize()
  """
  
  def __init__(self, filepath: str, row_class: type, buffer_size: int = None):
    self._filepath = filepath
    self._row_class = row_class
    self._buffer_size = buffer_size if buffer_size is not None else CRAWLER_HARDCODED_CONFIG.APPEND_TO_MAP_FILES_EVERY_X_LINES
    self._buffer: list = []
    self._file_handle = None
    self._csv_writer = None
    self._header_written = False
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
  
  def write_header(self) -> None:
    """Write CSV header atomically (temp file + rename). Opens file for subsequent appends."""
    field_names = [f.name for f in fields(self._row_class)]
    temp_path = self._filepath + ".tmp"
    with open(temp_path, 'w', newline='', encoding='utf-8') as f:
      writer = csv.writer(f)
      writer.writerow(field_names)
    os.replace(temp_path, self._filepath)
    self._file_handle = open(self._filepath, 'a', newline='', encoding='utf-8')
    self._csv_writer = csv.writer(self._file_handle)
    self._header_written = True
  
  def append_row(self, row) -> None:
    """Add row to buffer, flush if buffer size reached."""
    if not self._header_written: self.write_header()
    self._buffer.append(row)
    if len(self._buffer) >= self._buffer_size: self.flush()
  
  def flush(self) -> None:
    """Write buffered rows to file."""
    if not self._buffer or not self._csv_writer: return
    for row in self._buffer:
      row_dict = asdict(row) if hasattr(row, '__dataclass_fields__') else row
      field_names = [f.name for f in fields(self._row_class)]
      values = [row_dict.get(name, '') for name in field_names]
      self._csv_writer.writerow(values)
    self._file_handle.flush()
    self._buffer.clear()
  
  def finalize(self) -> None:
    """Flush remaining buffer and close file."""
    self.flush()
    if self._file_handle:
      self._file_handle.close()
      self._file_handle = None
      self._csv_writer = None

# ----------------------------------------- END: MapFileWriter Class --------------------------------------------------


# ----------------------------------------- START: Read Functions -----------------------------------------------------

def _parse_int(value: str, default: int = 0) -> int:
  """Parse string to int, return default if empty or invalid."""
  if not value or value.strip() == '': return default
  try: return int(value)
  except (ValueError, TypeError): return default

def _read_map_file(filepath: str, row_class: type) -> list:
  """Generic CSV reader that returns list of dataclass instances."""
  if not os.path.exists(filepath): return []
  result = []
  field_info = {f.name: f.type for f in fields(row_class)}
  try:
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
      reader = csv.DictReader(f)
      for row in reader:
        kwargs = {}
        for name, ftype in field_info.items():
          value = row.get(name, '')
          if ftype == int: kwargs[name] = _parse_int(value)
          else: kwargs[name] = value if value is not None else ''
        result.append(row_class(**kwargs))
  except Exception:
    return []  # Fallback to mode=full on corrupted file (B7)
  return result

def read_sharepoint_map(filepath: str) -> list:
  """Read sharepoint_map.csv, return list of SharePointMapRow."""
  return _read_map_file(filepath, SharePointMapRow)

def read_files_map(filepath: str) -> list:
  """Read files_map.csv, return list of FilesMapRow."""
  return _read_map_file(filepath, FilesMapRow)

def read_vectorstore_map(filepath: str) -> list:
  """Read vectorstore_map.csv, return list of VectorStoreMapRow."""
  return _read_map_file(filepath, VectorStoreMapRow)

# ----------------------------------------- END: Read Functions -------------------------------------------------------


# ----------------------------------------- START: Change Detection ---------------------------------------------------

def is_file_changed(sp: SharePointMapRow, local: FilesMapRow) -> bool:
  """
  Check if file has changed by comparing 4 fields (V2CR-FR-02).
  Used by download step for change detection.
  """
  return (
    sp.filename != local.filename or
    sp.server_relative_url != local.server_relative_url or
    sp.file_size != local.file_size or
    sp.last_modified_utc != local.last_modified_utc
  )

def is_file_changed_for_embed(files_row: FilesMapRow, vs_row: VectorStoreMapRow) -> bool:
  """
  Check if file has changed for embed step (2 fields only).
  Used by embed step to detect content changes.
  """
  return (
    files_row.file_size != vs_row.file_size or
    files_row.last_modified_utc != vs_row.last_modified_utc
  )

def detect_changes(sharepoint_items: list, local_items: list) -> ChangeDetectionResult:
  """
  Compare SharePoint state vs local state using sharepoint_unique_file_id as key.
  Implements V2CR-FR-01: Change detection by immutable ID.
  
  Args:
    sharepoint_items: list[SharePointMapRow] from current SharePoint scan
    local_items: list[FilesMapRow] from files_map.csv
    
  Returns:
    ChangeDetectionResult with added, removed, changed, unchanged lists
  """
  sp_by_id = {item.sharepoint_unique_file_id: item for item in sharepoint_items}
  local_by_id = {item.sharepoint_unique_file_id: item for item in local_items}
  
  sp_ids = set(sp_by_id.keys())
  local_ids = set(local_by_id.keys())
  
  added_ids = sp_ids - local_ids
  removed_ids = local_ids - sp_ids
  common_ids = sp_ids & local_ids
  
  added = [sp_by_id[uid] for uid in added_ids]
  removed = [local_by_id[uid] for uid in removed_ids]
  changed = []
  unchanged = []
  
  for uid in common_ids:
    sp_item = sp_by_id[uid]
    local_item = local_by_id[uid]
    if is_file_changed(sp_item, local_item):
      changed.append(sp_item)
    else:
      unchanged.append(local_item)
  
  return ChangeDetectionResult(added=added, removed=removed, changed=changed, unchanged=unchanged)

# ----------------------------------------- END: Change Detection -----------------------------------------------------


# ----------------------------------------- START: Conversion Helpers -------------------------------------------------

def sharepoint_map_row_to_files_map_row(sp_row: SharePointMapRow, file_relative_path: str = "", downloaded_utc: str = "", downloaded_timestamp: int = 0, sharepoint_error: str = "", processing_error: str = "") -> FilesMapRow:
  """Convert SharePointMapRow to FilesMapRow for files_map.csv."""
  return FilesMapRow(
    sharepoint_listitem_id=sp_row.sharepoint_listitem_id,
    sharepoint_unique_file_id=sp_row.sharepoint_unique_file_id,
    filename=sp_row.filename,
    file_type=sp_row.file_type,
    server_relative_url=sp_row.server_relative_url,
    file_relative_path=file_relative_path,
    file_size=sp_row.file_size,
    last_modified_utc=sp_row.last_modified_utc,
    last_modified_timestamp=sp_row.last_modified_timestamp,
    downloaded_utc=downloaded_utc,
    downloaded_timestamp=downloaded_timestamp,
    sharepoint_error=sharepoint_error,
    processing_error=processing_error
  )

def files_map_row_to_vectorstore_map_row(files_row: FilesMapRow, openai_file_id: str = "", vector_store_id: str = "", uploaded_utc: str = "", uploaded_timestamp: int = 0, embedded_utc: str = "", embedded_timestamp: int = 0, embedding_error: str = "") -> VectorStoreMapRow:
  """Convert FilesMapRow to VectorStoreMapRow for vectorstore_map.csv."""
  return VectorStoreMapRow(
    openai_file_id=openai_file_id,
    vector_store_id=vector_store_id,
    file_relative_path=files_row.file_relative_path,
    sharepoint_listitem_id=files_row.sharepoint_listitem_id,
    sharepoint_unique_file_id=files_row.sharepoint_unique_file_id,
    filename=files_row.filename,
    file_type=files_row.file_type,
    file_size=files_row.file_size,
    last_modified_utc=files_row.last_modified_utc,
    last_modified_timestamp=files_row.last_modified_timestamp,
    downloaded_utc=files_row.downloaded_utc,
    downloaded_timestamp=files_row.downloaded_timestamp,
    uploaded_utc=uploaded_utc,
    uploaded_timestamp=uploaded_timestamp,
    embedded_utc=embedded_utc,
    embedded_timestamp=embedded_timestamp,
    sharepoint_error=files_row.sharepoint_error,
    processing_error=files_row.processing_error,
    embedding_error=embedding_error
  )

# ----------------------------------------- END: Conversion Helpers ---------------------------------------------------
