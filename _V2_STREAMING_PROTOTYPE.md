# V2 Streaming Prototype

## Overview

The V2 streaming prototype implements a centralized file-based streaming system where:
- All streaming endpoints write logs to files AND stream to clients
- A monitor endpoint can attach to any active or completed job and stream the same data
- Multiple workers can run multiple streaming jobs in parallel
- Control endpoint can pause, resume, or cancel jobs
- Global sequential `sj_id` (streaming job ID) across all endpoints

## Key Differences from V1

| Feature | V1 | V2 |
|---------|----|----|
| ID Format | `endpoint_timestamp_pid_reqnum` | Global sequential integer (`sj_id`) |
| Log Storage | State files only (no content) | Full log content in files |
| Monitor | Not supported | Can attach and stream any job |
| File Location | Flat `/jobs/` folder | `/jobs/[router]/[endpoint]/` hierarchy |
| Multiple clients | Single consumer | Multiple monitors can attach |

## Architecture

### Core Components

1. **Job ID Generation** (`common_job_functions.py`)
   - Global sequential `sj_id` starting from 1
   - Scans last 1000 files to find highest ID
   - Race condition handled by file creation failure + retry

2. **Log File Management** (`common_job_functions.py`)
   - Single centralized write function
   - Atomic append operations
   - State transitions via file rename

3. **Streaming Endpoint** (`testrouter2.py`)
   - Writes to log file AND yields to HTTP stream
   - Checks control files on each iteration
   - Returns `sj_id` and monitor URL in header

4. **Monitor Endpoint** (`testrouter2.py`)
   - Tails log file and yields chunks
   - Works for running, completed, or canceled jobs
   - Multiple monitors can attach to same job

5. **Control Endpoint** (`testrouter2.py`)
   - Creates control request files
   - Streaming endpoint polls and reacts

## File Structure

### Job Files Location

```
PERSISTENT_STORAGE_PATH/jobs/
├── testrouter2/
│   └── streaming01/
│       ├── 2025-11-26_14-20-30_streaming01_1.running      # Active job with log content
│       ├── 2025-11-26_14-21-00_streaming01_2.completed    # Finished job with full log
│       ├── 2025-11-26_14-22-00_streaming01_3.canceled     # Canceled job with partial log
│       ├── 2025-11-26_14-23-00_streaming01_4.running      # Another active job
│       ├── 2025-11-26_14-23-00_streaming01_4.pause_requested  # Control file
│       └── 2025-11-26_14-24-00_streaming01_5.running
└── another_router/
    └── another_endpoint/
        ├── 2025-11-26_14-25-00_another_endpoint_6.running
        └── 2025-11-26_14-26-00_another_endpoint_7.completed
```

### File Naming Format

```
[TIMESTAMP]_[ENDPOINT_NAME]_[SJ_ID].[state]
```

**Example:** `2025-11-26_14-20-30_streaming01_42.running`

**Components:**
- `TIMESTAMP` - When the job was created (YYYY-MM-DD_HH-MM-SS)
- `ENDPOINT_NAME` - Name of the streaming endpoint
- `SJ_ID` - Global sequential streaming job ID

**States:**
- `.running` - Active job, contains log content
- `.completed` - Finished successfully
- `.canceled` - Stopped by user
- `.pause_requested` - Control: request pause
- `.resume_requested` - Control: request resume
- `.cancel_requested` - Control: request cancel

### File Content Example

**Filename:** `2025-11-26_14-20-30_streaming01_42.running`

```
# Streaming Job 42
# Router: testrouter2
# Endpoint: streaming01
# Created: 2025-11-26T14:20:30.123456

<header_json>
{
  "sj_id": 42,
  "monitor_url": "/streaming_jobs/monitor?sj_id=42",
  "total": 20
}
</header_json>
<log>
[ 1 / 20 ] Processing 'document_001.pdf'...
  OK.
[ 2 / 20 ] Processing 'document_002.pdf'...
  FAIL: Simulated error
[ 3 / 20 ] Processing 'document_003.pdf'...
  OK.
</log>
<footer_json>
{
  "result": "partial",
  "state": "completed",
  "sj_id": 42,
  "total": 20,
  "processed": 18,
  "failed": 2
}
</footer_json>
```

## SJ_ID Generation Algorithm

### Process

1. Scan all files in `PERSISTENT_STORAGE_PATH/jobs/**/*`
2. Filter files with valid extensions (`.running`, `.completed`, `.canceled`, etc.)
3. Sort by modification time (newest first)
4. Take last 1000 files
5. Extract `sj_id` from filenames using regex `^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_[^_]+_(\d+)\.[state]$`
6. Find maximum `sj_id`
7. Return `max_sj_id + 1`

### Race Condition Handling

If two workers generate the same `sj_id` simultaneously:

```python
# Worker 1: sj_id = 42, creates file successfully
# File: 2025-11-26_14-20-30_streaming01_42.running
success = create_streaming_job_file(..., sj_id=42)  # Returns True

# Worker 2: sj_id = 42, file already exists (same timestamp collision)
success = create_streaming_job_file(..., sj_id=42)  # Returns False

# Worker 2 retries: sj_id = 43
sj_id = generate_streaming_job_id(...)  # Returns 43 (scans again)
# File: 2025-11-26_14-20-30_streaming01_43.running
success = create_streaming_job_file(..., sj_id=43)  # Returns True
```

## API Endpoints

### Start Streaming Job

```
GET /testrouter2/streaming01?format=stream&files=20
```

**Parameters:**
- `format=stream` - Enable streaming response
- `files` - Number of files to simulate (default: 20)

**Response:** `text/event-stream; charset=utf-8`

**Header JSON:**
```json
{
  "sj_id": 42,
  "monitor_url": "/streaming_jobs/monitor?sj_id=42",
  "total": 20
}
```

### Monitor Streaming Job

```
GET /streaming_jobs/monitor?sj_id=42
```

**Parameters:**
- `sj_id` - Streaming job ID to monitor

**Behavior:**
1. Finds job file by scanning `/jobs/**/[sj_id].*`
2. Opens the log file and reads existing content
3. Yields content as chunks
4. If job is still running, waits for new data
5. When job completes/cancels, stops streaming

**Response:** `text/event-stream; charset=utf-8` (same content as original stream)

### Control Streaming Job

```
GET /streaming_jobs/control?sj_id=42&action=pause
GET /streaming_jobs/control?sj_id=42&action=resume
GET /streaming_jobs/control?sj_id=42&action=cancel
```

**Parameters:**
- `sj_id` - Streaming job ID
- `action` - One of: `pause`, `resume`, `cancel`

**Response:**
```json
{
  "success": true,
  "sj_id": 42,
  "action": "pause",
  "message": "Pause requested for job 42"
}
```

### List Streaming Jobs

```
GET /streaming_jobs?format=json
GET /streaming_jobs?format=html
GET /streaming_jobs?router=testrouter2
GET /streaming_jobs?state=running
```

**Parameters:**
- `format` - Response format (`json`, `html`, `ui`)
- `router` - Filter by router name
- `endpoint` - Filter by endpoint name
- `state` - Filter by state (`running`, `completed`, `canceled`)

**Response:**
```json
{
  "jobs": [
    {
      "sj_id": 42,
      "router": "testrouter2",
      "endpoint": "streaming01",
      "state": "running",
      "created": "2025-11-26T14:20:30"
    },
    {
      "sj_id": 41,
      "router": "testrouter2",
      "endpoint": "streaming01",
      "state": "completed",
      "created": "2025-11-26T14:15:00"
    }
  ],
  "count": 2
}
```

## Data Flow Diagrams

### Streaming + Monitor Parallel Flow

```
streaming01 endpoint              Log File                  monitor endpoint
      │                              │                              │
      ├─── write header ───────────►│                              │
      ├─── yield header ──► Client1  │                              │
      │                              │                              │
      ├─── write log line 1 ───────►│                              │
      ├─── yield log line 1 ► Client1│                              │
      │                              │                              │
      │                              │◄─── read all ───────────────┤
      │                              │────► yield to Client2 ──────►│
      │                              │                              │
      ├─── write log line 2 ───────►│                              │
      ├─── yield log line 2 ► Client1│                              │
      │                              │◄─── read new data ──────────┤
      │                              │────► yield to Client2 ──────►│
      │                              │                              │
      ├─── write footer ───────────►│                              │
      ├─── yield footer ──► Client1  │                              │
      ├─── rename .running→.completed│                              │
      │                              │◄─── detect completed ───────┤
      │                              │────► stop streaming ────────►│
```

### Control Flow (Pause/Resume)

```
streaming01            Control Endpoint          Control Files
     │                        │                        │
     │                        │◄── GET ?action=pause   │
     │                        ├── create ─────────────►│ 42.pause_requested
     │                        │                        │
     │◄── check control files ├────────────────────────│
     ├── detect pause_requested                        │
     ├── delete ──────────────────────────────────────►│ (remove pause_requested)
     ├── rename .running → .paused                     │
     │                        │                        │
     │   [PAUSED - polling]   │                        │
     │                        │                        │
     │                        │◄── GET ?action=resume  │
     │                        ├── create ─────────────►│ 42.resume_requested
     │                        │                        │
     │◄── check control files ├────────────────────────│
     ├── detect resume_requested                       │
     ├── delete ──────────────────────────────────────►│ (remove resume_requested)
     ├── rename .paused → .running                     │
     │                        │                        │
     │   [RUNNING]            │                        │
```

## Code Implementation

### common_job_functions.py - V2 Streaming Functions

```python
# ----------------------------------------- START: V2 Streaming ------------------------------------------

import os
import re
import glob
import datetime
from typing import Literal, Optional, List, Dict

# Type alias for job states
JobState = Literal["running", "paused", "completed", "canceled"]
ControlState = Literal["pause_requested", "resume_requested", "cancel_requested"]
AllStates = Literal["running", "paused", "completed", "canceled", 
                    "pause_requested", "resume_requested", "cancel_requested"]


def generate_streaming_job_id(persistent_storage_path: str) -> int:
    """
    Generate next streaming job ID by scanning existing job files.
    
    Algorithm:
    1. Scan all files in PERSISTENT_STORAGE_PATH/jobs/**/* folders
    2. Filter files with valid extensions
    3. Sort by modification time (newest first), take last 1000
    4. Extract sj_id from filenames, find highest
    5. Return highest + 1
    
    Args:
        persistent_storage_path: Base storage path
    
    Returns:
        Next sequential sj_id (starts at 1 if no jobs exist)
    """
    from hardcoded_config import CRAWLER_HARDCODED_CONFIG
    
    jobs_folder = os.path.join(
        persistent_storage_path,
        CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER
    )
    
    # Create jobs folder if it doesn't exist
    os.makedirs(jobs_folder, exist_ok=True)
    
    # Get all job files recursively
    pattern = os.path.join(jobs_folder, "**", "*.*")
    all_files = glob.glob(pattern, recursive=True)
    
    # Filter only job files with valid extensions
    valid_extensions = {
        '.running', '.paused', '.completed', '.canceled',
        '.pause_requested', '.resume_requested', '.cancel_requested'
    }
    job_files = [
        f for f in all_files 
        if os.path.splitext(f)[1] in valid_extensions
    ]
    
    if not job_files:
        return 1
    
    # Sort by modification time (newest first) and take last 1000
    job_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    recent_files = job_files[:1000]
    
    # Extract sj_id from filenames and find max
    # Filename format: [TIMESTAMP]_[ENDPOINT]_[SJ_ID].[state]
    max_sj_id = 0
    for filepath in recent_files:
        filename = os.path.basename(filepath)
        # Extract sj_id from filename: 2025-11-26_14-20-30_streaming01_42.running
        match = re.match(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_[^_]+_(\d+)\.', filename)
        if match:
            sj_id = int(match.group(1))
            max_sj_id = max(max_sj_id, sj_id)
    
    return max_sj_id + 1


def get_streaming_job_folder(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str
) -> str:
    """
    Get folder path for streaming job files.
    Creates folder if it doesn't exist.
    
    Returns:
        Path: PERSISTENT_STORAGE_PATH/jobs/[router]/[endpoint]/
    """
    from hardcoded_config import CRAWLER_HARDCODED_CONFIG
    
    folder = os.path.join(
        persistent_storage_path,
        CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER,
        router_name,
        endpoint_name
    )
    os.makedirs(folder, exist_ok=True)
    return folder


def get_streaming_job_file_path(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str,
    sj_id: int,
    state: AllStates,
    timestamp: str = None
) -> str:
    """
    Build full path to streaming job file.
    
    Args:
        persistent_storage_path: Base storage path
        router_name: Router name (e.g., "testrouter2")
        endpoint_name: Endpoint name (e.g., "streaming01")
        sj_id: Streaming job ID (integer)
        state: File state extension
        timestamp: Optional timestamp (YYYY-MM-DD_HH-MM-SS), required for new files
    
    Returns:
        Full path: PERSISTENT_STORAGE_PATH/jobs/[router]/[endpoint]/[timestamp]_[endpoint]_[sj_id].[state]
    """
    folder = get_streaming_job_folder(persistent_storage_path, router_name, endpoint_name)
    if timestamp:
        return os.path.join(folder, f"{timestamp}_{endpoint_name}_{sj_id}.{state}")
    else:
        # For finding existing files, we need to search by sj_id pattern
        return os.path.join(folder, f"*_{endpoint_name}_{sj_id}.{state}")


def create_streaming_job_file(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str,
    sj_id: int,
    state: AllStates = "running"
) -> tuple[bool, str]:
    """
    Create streaming job file with initial metadata header.
    
    Uses exclusive creation mode ('x') to fail if file already exists.
    This handles race conditions - only one worker can create the file.
    
    Args:
        persistent_storage_path: Base storage path
        router_name: Router name
        endpoint_name: Endpoint name
        sj_id: Streaming job ID
        state: Initial state (default: "running")
    
    Returns:
        Tuple of (success: bool, timestamp: str)
        - True and timestamp if created successfully
        - False and empty string if file already exists
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = get_streaming_job_file_path(
        persistent_storage_path, router_name, endpoint_name, sj_id, state, timestamp
    )
    
    try:
        with open(file_path, 'x', encoding='utf-8') as f:
            f.write(f"# Streaming Job {sj_id}\n")
            f.write(f"# Router: {router_name}\n")
            f.write(f"# Endpoint: {endpoint_name}\n")
            f.write(f"# Created: {datetime.datetime.now().isoformat()}\n\n")
        return True, timestamp
    except FileExistsError:
        return False, ""


def find_streaming_job_file(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str,
    sj_id: int,
    state: str
) -> Optional[str]:
    """
    Find streaming job file by sj_id and state.
    
    Searches for files matching pattern: *_[endpoint]_[sj_id].[state]
    
    Returns:
        Full file path if found, None otherwise
    """
    folder = get_streaming_job_folder(persistent_storage_path, router_name, endpoint_name)
    pattern = os.path.join(folder, f"*_{endpoint_name}_{sj_id}.{state}")
    matches = glob.glob(pattern)
    return matches[0] if matches else None


def create_streaming_job_control_file(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str,
    sj_id: int,
    timestamp: str,
    control_state: str
) -> bool:
    """
    Create a control file (pause_requested, resume_requested, cancel_requested).
    
    Control files are empty marker files that signal the streaming job to take action.
    Uses the same timestamp as the original job file.
    
    Args:
        persistent_storage_path: Base storage path
        router_name: Router name
        endpoint_name: Endpoint name
        sj_id: Streaming job ID
        timestamp: Timestamp from the original job file
        control_state: One of "pause_requested", "resume_requested", "cancel_requested"
    
    Returns:
        True if created, False if already exists
    """
    folder = get_streaming_job_folder(persistent_storage_path, router_name, endpoint_name)
    file_path = os.path.join(folder, f"{timestamp}_{endpoint_name}_{sj_id}.{control_state}")
    
    try:
        with open(file_path, 'x', encoding='utf-8') as f:
            f.write(datetime.datetime.now().isoformat())
        return True
    except FileExistsError:
        return False


def write_streaming_job_log(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str,
    sj_id: int,
    message: str
):
    """
    Append message to streaming job log file atomically.
    
    This is the SINGLE CENTRALIZED function that writes to job files.
    All streaming endpoints must use this function.
    
    Writes to the current state file (.running or .paused).
    
    Args:
        persistent_storage_path: Base storage path
        router_name: Router name
        endpoint_name: Endpoint name
        sj_id: Streaming job ID
        message: Log message to append (include newlines as needed)
    """
    # Try .running first, then .paused
    for state in ["running", "paused"]:
        log_file = find_streaming_job_file(
            persistent_storage_path, router_name, endpoint_name, sj_id, state
        )
        if log_file:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(message)
                f.flush()
            return
    
    # If neither exists, this is an error - file should have been created
    raise FileNotFoundError(f"No job file found for sj_id={sj_id}")


def rename_streaming_job_file(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str,
    sj_id: int,
    old_state: str,
    new_state: str
) -> bool:
    """
    Rename streaming job file from one state to another.
    
    Example: .running → .completed
    Preserves timestamp and endpoint in filename.
    
    Args:
        persistent_storage_path: Base storage path
        router_name: Router name
        endpoint_name: Endpoint name
        sj_id: Streaming job ID
        old_state: Current state extension
        new_state: New state extension
    
    Returns:
        True if renamed successfully, False otherwise
    """
    old_path = find_streaming_job_file(
        persistent_storage_path, router_name, endpoint_name, sj_id, old_state
    )
    
    if not old_path:
        return False
    
    # Replace old state extension with new state
    new_path = old_path.rsplit('.', 1)[0] + f".{new_state}"
    
    try:
        os.rename(old_path, new_path)
        return True
    except (FileNotFoundError, OSError):
        return False


def delete_streaming_job_file(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str,
    sj_id: int,
    state: str
) -> bool:
    """
    Delete streaming job state file.
    
    Used to remove control request files after processing.
    
    Returns:
        True if deleted successfully, False if file doesn't exist
    """
    file_path = find_streaming_job_file(
        persistent_storage_path, router_name, endpoint_name, sj_id, state
    )
    
    if not file_path:
        return False
    
    try:
        os.remove(file_path)
        return True
    except FileNotFoundError:
        return False


def streaming_job_file_exists(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str,
    sj_id: int,
    state: str
) -> bool:
    """
    Check if streaming job state file exists.
    
    Used to check for control request files.
    """
    file_path = find_streaming_job_file(
        persistent_storage_path, router_name, endpoint_name, sj_id, state
    )
    return file_path is not None


def get_streaming_job_current_state(
    persistent_storage_path: str,
    router_name: str,
    endpoint_name: str,
    sj_id: int
) -> Optional[JobState]:
    """
    Get current state of streaming job.
    
    Returns:
        "running", "paused", "completed", "canceled", or None if job doesn't exist
    """
    for state in ["running", "paused", "completed", "canceled"]:
        if find_streaming_job_file(
            persistent_storage_path, router_name, endpoint_name, sj_id, state
        ):
            return state
    return None


def find_streaming_job_by_id(
    persistent_storage_path: str,
    sj_id: int
) -> Optional[Dict]:
    """
    Find streaming job by sj_id across all routers/endpoints.
    
    Scans all job folders to find the file with this sj_id.
    Filename format: [TIMESTAMP]_[ENDPOINT]_[SJ_ID].[state]
    
    Args:
        persistent_storage_path: Base storage path
        sj_id: Streaming job ID to find
    
    Returns:
        Dict with router_name, endpoint_name, state, file_path, timestamp, or None if not found
    """
    from hardcoded_config import CRAWLER_HARDCODED_CONFIG
    
    jobs_folder = os.path.join(
        persistent_storage_path,
        CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER
    )
    
    if not os.path.exists(jobs_folder):
        return None
    
    # Search for the sj_id file using pattern: *_*_[sj_id].[state]
    valid_states = {'running', 'paused', 'completed', 'canceled'}
    
    for root, dirs, files in os.walk(jobs_folder):
        for f in files:
            # Match pattern: TIMESTAMP_ENDPOINT_SJID.state
            match = re.match(r'^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_([^_]+)_(\d+)\.(\w+)$', f)
            if match:
                file_timestamp = match.group(1)
                file_endpoint = match.group(2)
                file_sj_id = int(match.group(3))
                file_state = match.group(4)
                
                if file_sj_id == sj_id and file_state in valid_states:
                    # Found it! Extract router from path
                    rel_path = os.path.relpath(root, jobs_folder)
                    parts = rel_path.split(os.sep)
                    
                    if len(parts) >= 2:
                        router_name = parts[0]
                        endpoint_name = parts[1]
                        
                        return {
                            "sj_id": sj_id,
                            "router_name": router_name,
                            "endpoint_name": endpoint_name,
                            "state": file_state,
                            "timestamp": file_timestamp,
                            "file_path": os.path.join(root, f)
                        }
    
    return None


def list_streaming_jobs(
    persistent_storage_path: str,
    router_filter: Optional[str] = None,
    endpoint_filter: Optional[str] = None,
    state_filter: Optional[str] = None
) -> List[Dict]:
    """
    List all streaming jobs with optional filters.
    
    Filename format: [TIMESTAMP]_[ENDPOINT]_[SJ_ID].[state]
    
    Args:
        persistent_storage_path: Base storage path
        router_filter: Filter by router name
        endpoint_filter: Filter by endpoint name
        state_filter: Filter by state
    
    Returns:
        List of job dictionaries with sj_id, router, endpoint, state, created
    """
    from hardcoded_config import CRAWLER_HARDCODED_CONFIG
    
    jobs_folder = os.path.join(
        persistent_storage_path,
        CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_JOBS_SUBFOLDER
    )
    
    if not os.path.exists(jobs_folder):
        return []
    
    jobs = []
    valid_states = {'running', 'paused', 'completed', 'canceled'}
    
    for root, dirs, files in os.walk(jobs_folder):
        for f in files:
            # Parse filename: TIMESTAMP_ENDPOINT_SJID.state
            match = re.match(r'^(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})_([^_]+)_(\d+)\.(running|paused|completed|canceled)$', f)
            if not match:
                continue
            
            file_timestamp = match.group(1)
            file_endpoint = match.group(2)
            sj_id = int(match.group(3))
            state = match.group(4)
            
            # Extract router and endpoint from path
            rel_path = os.path.relpath(root, jobs_folder)
            parts = rel_path.split(os.sep)
            
            if len(parts) < 2:
                continue
            
            router_name = parts[0]
            endpoint_name = parts[1]
            
            # Apply filters
            if router_filter and router_name != router_filter:
                continue
            if endpoint_filter and endpoint_name != endpoint_filter:
                continue
            if state_filter and state != state_filter:
                continue
            
            # Convert timestamp from filename to ISO format
            # Input: 2025-11-26_14-20-30 -> Output: 2025-11-26T14:20:30
            date_part, time_part = file_timestamp.split('_')
            time_formatted = time_part.replace('-', ':')
            created = f"{date_part}T{time_formatted}"
            
            jobs.append({
                "sj_id": sj_id,
                "router": router_name,
                "endpoint": endpoint_name,
                "state": state,
                "created": created
            })
    
    # Sort by sj_id descending (newest first)
    jobs.sort(key=lambda j: j["sj_id"], reverse=True)
    
    return jobs

# ----------------------------------------- END: V2 Streaming ------------------------------------------
```

### testrouter2.py - V2 Streaming Router

```python
"""
V2 Streaming Test Router

Implements:
- /testrouter2/streaming01 - Test streaming endpoint
- /streaming_jobs/monitor - Monitor any streaming job
- /streaming_jobs/control - Pause/resume/cancel jobs
- /streaming_jobs - List all jobs
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
import asyncio
import json
import os
import random
from typing import Optional

from utils import log_function_header, log_function_footer
from common_job_functions import (
    generate_streaming_job_id,
    create_streaming_job_file,
    create_streaming_job_control_file,
    find_streaming_job_file,
    write_streaming_job_log,
    rename_streaming_job_file,
    delete_streaming_job_file,
    streaming_job_file_exists,
    get_streaming_job_current_state,
    find_streaming_job_by_id,
    list_streaming_jobs,
    get_streaming_job_file_path
)

router = APIRouter()

# Global config reference (set by app.py)
config = None


# =============================================================================
# STREAMING TEST ENDPOINT
# =============================================================================

@router.get('/testrouter2/streaming01')
async def streaming01(request: Request):
    """
    V2 Streaming Test Endpoint
    
    Simulates file processing with streaming output.
    Writes to log file AND streams to client simultaneously.
    
    Parameters:
    - format: "stream" for streaming response, "json" for collected results
    - files: Number of files to simulate (default: 20)
    
    Examples:
    - GET /testrouter2/streaming01?format=stream&files=20
    - GET /testrouter2/streaming01?format=json&files=10
    """
    function_name = 'streaming01()'
    log_data = log_function_header(function_name)
    request_params = dict(request.query_params)
    
    response_format = request_params.get('format', 'stream')
    file_count = int(request_params.get('files', '20'))
    
    if response_format != 'stream':
        # Non-streaming: just return JSON
        await log_function_footer(log_data)
        return JSONResponse({
            "message": "Use format=stream for streaming response",
            "files": file_count
        })
    
    # Generate unique job ID with retry on collision
    max_retries = 3
    sj_id = None
    job_timestamp = None
    
    for attempt in range(max_retries):
        sj_id = generate_streaming_job_id(config.LOCAL_PERSISTENT_STORAGE_PATH)
        success, job_timestamp = create_streaming_job_file(
            config.LOCAL_PERSISTENT_STORAGE_PATH,
            "testrouter2", "streaming01", sj_id, "running"
        )
        if success:
            break
        # Collision - another worker got this ID, retry
        sj_id = None
        job_timestamp = None
    
    if sj_id is None:
        await log_function_footer(log_data)
        return JSONResponse(
            {"error": "Failed to create streaming job after retries"},
            status_code=500
        )
    
    async def generate_stream():
        """Generator that writes to file AND yields to HTTP stream"""
        
        router_name = "testrouter2"
        endpoint_name = "streaming01"
        
        simulated_files = [f"document_{i:03d}.pdf" for i in range(1, file_count + 1)]
        processed_files = []
        failed_files = []
        final_state = "completed"
        final_result = "success"
        
        # ----- HEADER SECTION -----
        header = {
            "sj_id": sj_id,
            "monitor_url": f"/streaming_jobs/monitor?sj_id={sj_id}",
            "total": file_count
        }
        header_text = f"<header_json>\n{json.dumps(header, indent=2)}\n</header_json>\n"
        
        write_streaming_job_log(
            config.LOCAL_PERSISTENT_STORAGE_PATH,
            router_name, endpoint_name, sj_id, header_text
        )
        yield header_text
        
        # ----- LOG SECTION START -----
        log_start = "<log>\n"
        write_streaming_job_log(
            config.LOCAL_PERSISTENT_STORAGE_PATH,
            router_name, endpoint_name, sj_id, log_start
        )
        yield log_start
        
        # ----- PROCESS ITEMS -----
        for index, filename in enumerate(simulated_files, start=1):
            
            # Check for cancel request
            if streaming_job_file_exists(
                config.LOCAL_PERSISTENT_STORAGE_PATH,
                router_name, endpoint_name, sj_id, "cancel_requested"
            ):
                cancel_msg = "  Cancel requested, stopping...\n"
                write_streaming_job_log(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, cancel_msg
                )
                yield cancel_msg
                
                delete_streaming_job_file(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, "cancel_requested"
                )
                final_state = "canceled"
                final_result = "cancelled"
                break
            
            # Check for pause request
            if streaming_job_file_exists(
                config.LOCAL_PERSISTENT_STORAGE_PATH,
                router_name, endpoint_name, sj_id, "pause_requested"
            ):
                pause_msg = "  Pause requested, pausing...\n"
                write_streaming_job_log(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, pause_msg
                )
                yield pause_msg
                
                delete_streaming_job_file(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, "pause_requested"
                )
                rename_streaming_job_file(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, "running", "paused"
                )
            
            # Wait while paused
            while streaming_job_file_exists(
                config.LOCAL_PERSISTENT_STORAGE_PATH,
                router_name, endpoint_name, sj_id, "paused"
            ):
                # Check for cancel while paused
                if streaming_job_file_exists(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, "cancel_requested"
                ):
                    cancel_msg = "  Cancel requested while paused, stopping...\n"
                    write_streaming_job_log(
                        config.LOCAL_PERSISTENT_STORAGE_PATH,
                        router_name, endpoint_name, sj_id, cancel_msg
                    )
                    yield cancel_msg
                    
                    delete_streaming_job_file(
                        config.LOCAL_PERSISTENT_STORAGE_PATH,
                        router_name, endpoint_name, sj_id, "cancel_requested"
                    )
                    delete_streaming_job_file(
                        config.LOCAL_PERSISTENT_STORAGE_PATH,
                        router_name, endpoint_name, sj_id, "paused"
                    )
                    final_state = "canceled"
                    final_result = "cancelled"
                    break
                
                # Check for resume request
                if streaming_job_file_exists(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, "resume_requested"
                ):
                    resume_msg = "  Resume requested, resuming...\n"
                    write_streaming_job_log(
                        config.LOCAL_PERSISTENT_STORAGE_PATH,
                        router_name, endpoint_name, sj_id, resume_msg
                    )
                    yield resume_msg
                    
                    delete_streaming_job_file(
                        config.LOCAL_PERSISTENT_STORAGE_PATH,
                        router_name, endpoint_name, sj_id, "resume_requested"
                    )
                    rename_streaming_job_file(
                        config.LOCAL_PERSISTENT_STORAGE_PATH,
                        router_name, endpoint_name, sj_id, "paused", "running"
                    )
                    break
                
                await asyncio.sleep(0.1)  # Poll every 100ms
            
            # Check if we were canceled while paused
            if final_state == "canceled":
                break
            
            # Process item
            progress_msg = f"[ {index} / {file_count} ] Processing '{filename}'...\n"
            write_streaming_job_log(
                config.LOCAL_PERSISTENT_STORAGE_PATH,
                router_name, endpoint_name, sj_id, progress_msg
            )
            yield progress_msg
            
            await asyncio.sleep(0.2)  # Simulate work
            
            # Simulate random failures (10% chance)
            if random.random() < 0.1:
                fail_msg = f"  FAIL: Simulated error for '{filename}'\n"
                write_streaming_job_log(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, fail_msg
                )
                yield fail_msg
                failed_files.append({"filename": filename, "error": "Simulated error"})
            else:
                ok_msg = "  OK.\n"
                write_streaming_job_log(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, ok_msg
                )
                yield ok_msg
                processed_files.append({"filename": filename, "size_bytes": random.randint(10000, 500000)})
        
        # ----- LOG SECTION END -----
        log_end = "</log>\n"
        write_streaming_job_log(
            config.LOCAL_PERSISTENT_STORAGE_PATH,
            router_name, endpoint_name, sj_id, log_end
        )
        yield log_end
        
        # ----- FOOTER SECTION -----
        if final_result != "cancelled" and failed_files:
            final_result = "partial"
        
        footer = {
            "result": final_result,
            "state": final_state,
            "sj_id": sj_id,
            "total": file_count,
            "processed": len(processed_files),
            "failed": len(failed_files),
            "processed_files": processed_files,
            "failed_files": failed_files
        }
        footer_text = f"<footer_json>\n{json.dumps(footer, indent=2)}\n</footer_json>\n"
        
        write_streaming_job_log(
            config.LOCAL_PERSISTENT_STORAGE_PATH,
            router_name, endpoint_name, sj_id, footer_text
        )
        yield footer_text
        
        # ----- FINALIZE STATE -----
        # Rename .running or .paused to final state
        for current_state in ["running", "paused"]:
            if streaming_job_file_exists(
                config.LOCAL_PERSISTENT_STORAGE_PATH,
                router_name, endpoint_name, sj_id, current_state
            ):
                rename_streaming_job_file(
                    config.LOCAL_PERSISTENT_STORAGE_PATH,
                    router_name, endpoint_name, sj_id, current_state, final_state
                )
                break
    
    await log_function_footer(log_data)
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream; charset=utf-8"
    )


# =============================================================================
# MONITOR ENDPOINT
# =============================================================================

@router.get('/streaming_jobs/monitor')
async def monitor_streaming_job(request: Request, sj_id: int):
    """
    Monitor a streaming job by tailing its log file.
    
    Can attach to:
    - Running jobs: streams live updates
    - Completed jobs: returns full log
    - Canceled jobs: returns partial log
    
    Parameters:
    - sj_id: Streaming job ID to monitor
    
    Example:
    - GET /streaming_jobs/monitor?sj_id=42
    """
    function_name = 'monitor_streaming_job()'
    log_data = log_function_header(function_name)
    
    # Find the job
    job_info = find_streaming_job_by_id(
        config.LOCAL_PERSISTENT_STORAGE_PATH,
        sj_id
    )
    
    if not job_info:
        await log_function_footer(log_data)
        return JSONResponse(
            {"error": f"Job {sj_id} not found"},
            status_code=404
        )
    
    router_name = job_info["router_name"]
    endpoint_name = job_info["endpoint_name"]
    file_path = job_info["file_path"]
    
    async def tail_log_file():
        """Tail the log file and yield chunks"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(4096)  # Read in 4KB chunks
                
                if chunk:
                    yield chunk
                else:
                    # No more data available
                    # Check if job is still active
                    current_state = get_streaming_job_current_state(
                        config.LOCAL_PERSISTENT_STORAGE_PATH,
                        router_name, endpoint_name, sj_id
                    )
                    
                    if current_state in ["running", "paused"]:
                        # Job still active, wait for more data
                        await asyncio.sleep(0.1)
                        
                        # Re-check file path in case it was renamed
                        new_job_info = find_streaming_job_by_id(
                            config.LOCAL_PERSISTENT_STORAGE_PATH,
                            sj_id
                        )
                        if new_job_info and new_job_info["file_path"] != file_path:
                            # File was renamed (state change), reopen
                            break
                    else:
                        # Job completed/canceled - do final read to catch any remaining content
                        final_chunk = f.read()
                        if final_chunk:
                            yield final_chunk
                        break
    
    await log_function_footer(log_data)
    return StreamingResponse(
        tail_log_file(),
        media_type="text/event-stream; charset=utf-8"
    )


# =============================================================================
# CONTROL ENDPOINT
# =============================================================================

@router.get('/streaming_jobs/control')
async def control_streaming_job(
    request: Request,
    sj_id: int,
    action: str
):
    """
    Control a streaming job (pause/resume/cancel).
    
    Parameters:
    - sj_id: Streaming job ID
    - action: One of "pause", "resume", "cancel"
    
    Examples:
    - GET /streaming_jobs/control?sj_id=42&action=pause
    - GET /streaming_jobs/control?sj_id=42&action=resume
    - GET /streaming_jobs/control?sj_id=42&action=cancel
    """
    function_name = 'control_streaming_job()'
    log_data = log_function_header(function_name)
    
    # Validate action
    valid_actions = ["pause", "resume", "cancel"]
    if action not in valid_actions:
        await log_function_footer(log_data)
        return JSONResponse(
            {"error": f"Invalid action '{action}'. Must be one of: {valid_actions}"},
            status_code=400
        )
    
    # Find the job
    job_info = find_streaming_job_by_id(
        config.LOCAL_PERSISTENT_STORAGE_PATH,
        sj_id
    )
    
    if not job_info:
        await log_function_footer(log_data)
        return JSONResponse(
            {"error": f"Job {sj_id} not found"},
            status_code=404
        )
    
    router_name = job_info["router_name"]
    endpoint_name = job_info["endpoint_name"]
    current_state = job_info["state"]
    
    # Validate state for action
    if current_state not in ["running", "paused"]:
        await log_function_footer(log_data)
        return JSONResponse(
            {"error": f"Cannot {action} job {sj_id} - job is {current_state}"},
            status_code=400
        )
    
    # Create control request file (uses same timestamp as original job)
    control_state = f"{action}_requested"
    job_timestamp = job_info["timestamp"]
    success = create_streaming_job_control_file(
        config.LOCAL_PERSISTENT_STORAGE_PATH,
        router_name, endpoint_name, sj_id, job_timestamp, control_state
    )
    
    await log_function_footer(log_data)
    
    if success:
        return JSONResponse({
            "success": True,
            "sj_id": sj_id,
            "action": action,
            "message": f"{action.capitalize()} requested for job {sj_id}"
        })
    else:
        return JSONResponse({
            "success": False,
            "sj_id": sj_id,
            "action": action,
            "message": f"{action.capitalize()} already requested for job {sj_id}"
        })


# =============================================================================
# LIST JOBS ENDPOINT
# =============================================================================

@router.get('/streaming_jobs')
async def list_jobs(
    request: Request,
    format: str = "json",
    router: Optional[str] = None,
    endpoint: Optional[str] = None,
    state: Optional[str] = None
):
    """
    List all streaming jobs with optional filters.
    
    Parameters:
    - format: Response format ("json", "html", "ui")
    - router: Filter by router name
    - endpoint: Filter by endpoint name
    - state: Filter by state ("running", "paused", "completed", "canceled")
    
    Examples:
    - GET /streaming_jobs?format=json
    - GET /streaming_jobs?state=running
    - GET /streaming_jobs?router=testrouter2&state=completed
    """
    function_name = 'list_jobs()'
    log_data = log_function_header(function_name)
    
    jobs = list_streaming_jobs(
        config.LOCAL_PERSISTENT_STORAGE_PATH,
        router_filter=router,
        endpoint_filter=endpoint,
        state_filter=state
    )
    
    await log_function_footer(log_data)
    
    if format == "json":
        return JSONResponse({
            "jobs": jobs,
            "count": len(jobs)
        })
    
    elif format == "html":
        # Simple HTML table
        html = "<html><body>"
        html += f"<h1>Streaming Jobs ({len(jobs)})</h1>"
        html += "<table border='1'><tr><th>SJ_ID</th><th>Router</th><th>Endpoint</th><th>State</th><th>Created</th><th>Actions</th></tr>"
        
        for job in jobs:
            html += f"<tr>"
            html += f"<td>{job['sj_id']}</td>"
            html += f"<td>{job['router']}</td>"
            html += f"<td>{job['endpoint']}</td>"
            html += f"<td>{job['state']}</td>"
            html += f"<td>{job['created']}</td>"
            html += f"<td>"
            html += f"<a href='/streaming_jobs/monitor?sj_id={job['sj_id']}'>Monitor</a> | "
            if job['state'] == 'running':
                html += f"<a href='/streaming_jobs/control?sj_id={job['sj_id']}&action=pause'>Pause</a> | "
                html += f"<a href='/streaming_jobs/control?sj_id={job['sj_id']}&action=cancel'>Cancel</a>"
            elif job['state'] == 'paused':
                html += f"<a href='/streaming_jobs/control?sj_id={job['sj_id']}&action=resume'>Resume</a> | "
                html += f"<a href='/streaming_jobs/control?sj_id={job['sj_id']}&action=cancel'>Cancel</a>"
            html += f"</td>"
            html += f"</tr>"
        
        html += "</table></body></html>"
        return HTMLResponse(html)
    
    else:
        return JSONResponse({
            "jobs": jobs,
            "count": len(jobs)
        })
```

### app.py - Router Registration

```python
# Add to router imports
from routers import testrouter2

# Add to router registration
app.include_router(testrouter2.router, tags=["testrouter2"])

# Pass config to testrouter2
testrouter2.config = config
```

## Usage Examples

### Start a Streaming Job

```bash
curl "http://localhost:8000/testrouter2/streaming01?format=stream&files=10"
```

**Response (streaming):**
```
<header_json>
{
  "sj_id": 42,
  "monitor_url": "/streaming_jobs/monitor?sj_id=42",
  "total": 10
}
</header_json>
<log>
[ 1 / 10 ] Processing 'document_001.pdf'...
  OK.
[ 2 / 10 ] Processing 'document_002.pdf'...
  OK.
...
</log>
<footer_json>
{
  "result": "success",
  "state": "completed",
  "sj_id": 42,
  "total": 10,
  "processed": 10,
  "failed": 0
}
</footer_json>
```

### Monitor a Running Job

```bash
# In another terminal, while job is running:
curl "http://localhost:8000/streaming_jobs/monitor?sj_id=42"
```

### Control a Job

```bash
# Pause
curl "http://localhost:8000/streaming_jobs/control?sj_id=42&action=pause"

# Resume
curl "http://localhost:8000/streaming_jobs/control?sj_id=42&action=resume"

# Cancel
curl "http://localhost:8000/streaming_jobs/control?sj_id=42&action=cancel"
```

### List All Jobs

```bash
# JSON format
curl "http://localhost:8000/streaming_jobs?format=json"

# Filter by state
curl "http://localhost:8000/streaming_jobs?state=running"

# HTML view
curl "http://localhost:8000/streaming_jobs?format=html"
```

## Advantages over V1

1. **Monitor capability**: Any client can attach and stream job output
2. **Full log persistence**: Completed jobs retain full log content
3. **Simpler IDs**: Sequential integers instead of complex strings
4. **Organized structure**: Jobs organized by router/endpoint
5. **Multi-worker safe**: File collision handled with retry
6. **Centralized logging**: Single `write_streaming_job_log()` function

## Limitations

1. **File I/O overhead**: Every log line writes to disk
2. **No queuing**: Jobs start immediately, no scheduling
3. **Simple search**: Finding jobs requires file system scan
4. **No cleanup**: Old completed jobs accumulate

## Future Enhancements (V3)

1. **Buffered writes**: Batch log lines before writing
2. **Auto-cleanup**: Remove old completed jobs

