# Logging V2 - Unified logger for FastAPI endpoints with optional streaming support
# Implements MiddlewareLogger class per _V2_SPEC_ROUTERS.md specification

import datetime, logging, os, sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
  from routers_v2.common_job_functions_v2 import StreamingJobWriter

# Configure logging for multi-worker environment
logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# Global request counter (LOG-IG-04: monotonically increasing)
_request_counter = 0

# Format milliseconds into a human-readable string
def format_milliseconds(millisecs: int) -> str:
  if millisecs < 1000: return f"{millisecs} ms"
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

@dataclass
class MiddlewareLogger:
  """
  Unified logger for FastAPI endpoints with optional streaming support.
  
  Implements LOG-FR-01 through LOG-FR-06 and LOG-IG-01 through LOG-IG-05 from specification.
  
  Usage:
    # Non-streaming endpoint
    logger = MiddlewareLogger.create()
    logger.log_function_header("my_endpoint()")
    logger.log_function_output("Processing...")
    logger.log_function_footer()
    
    # Streaming endpoint
    writer = StreamingJobWriter(...)
    logger = MiddlewareLogger.create(stream_job_writer=writer)
    sse = logger.log_function_header("my_endpoint()")
    if sse: yield sse
  """
  
  # Configuration (set at creation)
  log_inner_function_headers_and_footers: bool = True
  inner_log_indentation: int = 2
  stream_job_writer: Optional["StreamingJobWriter"] = None
  
  # State (managed internally)
  _function_name: str = ""
  _start_time: Optional[datetime.datetime] = None
  _request_number: int = 0
  _nesting_depth: int = 0
  _inner_stack: List[Tuple[str, datetime.datetime]] = field(default_factory=list)
  
  @classmethod
  def create(cls, log_inner_function_headers_and_footers: bool = True, inner_log_indentation: int = 2, stream_job_writer: Optional["StreamingJobWriter"] = None) -> "MiddlewareLogger":
    """Factory method. Increments global request counter (LOG-IG-04)."""
    global _request_counter
    _request_counter += 1
    instance = cls(
      log_inner_function_headers_and_footers=log_inner_function_headers_and_footers,
      inner_log_indentation=inner_log_indentation,
      stream_job_writer=stream_job_writer,
      _request_number=_request_counter,
      _inner_stack=[]
    )
    return instance
  
  def log_function_header(self, function_name: str) -> Optional[str]:
    """
    Log function start.
    - depth=0: Always logs, sets top-level function name and start time
    - depth>0: Logs only if log_inner_function_headers_and_footers=True
    Returns: SSE event string if stream_job_writer set and output logged, else None
    """
    now = datetime.datetime.now()
    
    if self._nesting_depth == 0:
      # Top-level function: always log, set state
      self._function_name = function_name
      self._start_time = now
      message = f"START: {function_name}..."
      self._log_to_console(message)
      self._nesting_depth = 1
      return self._emit_to_stream(message)
    else:
      # Nested function: push to stack, conditionally log
      self._inner_stack.append((function_name, now))
      self._nesting_depth += 1
      
      if self.log_inner_function_headers_and_footers:
        indented_message = self._apply_indentation(f"START: {function_name}...")
        self._log_to_console(indented_message)
        return self._emit_to_stream(indented_message)
      return None
  
  def log_function_output(self, output: str) -> Optional[str]:
    """
    Log intermediate output. Always logs regardless of nesting depth (LOG-FR-03).
    Applies indentation based on current nesting depth (LOG-FR-04).
    Returns: SSE event string if stream_job_writer set, else None
    """
    indented_message = self._apply_indentation(output)
    self._log_to_console(indented_message)
    return self._emit_to_stream(indented_message)
  
  def log_function_footer(self) -> Optional[str]:
    """
    Log function end.
    - depth>0: Pops from stack, logs if log_inner_function_headers_and_footers=True
    - depth=0: Logs total duration (should not decrement below 0)
    Returns: SSE event string if stream_job_writer set and output logged, else None
    """
    now = datetime.datetime.now()
    
    if self._nesting_depth <= 1:
      # Top-level function: log with total duration
      if self._start_time:
        ms = int((now - self._start_time).total_seconds() * 1000)
        duration = format_milliseconds(ms)
      else:
        duration = "0 ms"
      
      message = f"END: {self._function_name} ({duration})."
      self._log_to_console(message)
      self._nesting_depth = 0
      return self._emit_to_stream(message)
    else:
      # Nested function: pop from stack
      self._nesting_depth -= 1
      
      if self._inner_stack:
        inner_func_name, inner_start_time = self._inner_stack.pop()
        
        if self.log_inner_function_headers_and_footers:
          ms = int((now - inner_start_time).total_seconds() * 1000)
          duration = format_milliseconds(ms)
          indented_message = self._apply_indentation(f"END: {inner_func_name} ({duration}).")
          self._log_to_console(indented_message)
          return self._emit_to_stream(indented_message)
      return None
  
  def _apply_indentation(self, output: str) -> str:
    """Apply indentation based on nesting depth (LOG-FR-04). Depth 0 and 1 have no indentation."""
    if self._nesting_depth <= 1: return output
    indent = " " * (self.inner_log_indentation * (self._nesting_depth - 1))
    return indent + output
  
  def _log_to_console(self, message: str) -> None:
    """Write to server console using standard format (LOG-IG-03)."""
    process_id = os.getpid()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{timestamp},process {process_id},request {self._request_number},{self._function_name}] {message}")
  
  def _emit_to_stream(self, message: str) -> Optional[str]:
    """
    Emit to stream if writer is set (LOG-FR-05).
    Adds SSE-style timestamp prefix: [YYYY-MM-DD HH:MM:SS] MESSAGE
    Calls writer.emit_log() for dual output compliance (STREAM-FR-01).
    Returns SSE-formatted string or None.
    """
    if self.stream_job_writer is None: return None
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    timestamped_message = f"[{timestamp}] {message}"
    return self.stream_job_writer.emit_log(timestamped_message)
