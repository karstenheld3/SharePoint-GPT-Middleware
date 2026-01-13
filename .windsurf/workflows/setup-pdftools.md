---
description: Setup development tools (Python, Poppler, uv)
auto_execution_mode: 1
---

# Setup Development Tools

Run this workflow once to prepare the development environment.

## 1. Set Workspace Folder

```powershell
$workspaceFolder = (Get-Location).Path  # or set explicitly: $workspaceFolder = "E:\Dev\MyProject"
$toolsDir = "$workspaceFolder\.tools"
```

## 2. Verify Python Installation

```powershell
python --version
```

Expected: Python 3.10+ installed and in PATH.
If not installed: Ask user to install Python from https://python.org

## 3. Install Poppler Locally

Poppler provides `pdftoppm` for converting PDF pages to images.

### Check if already installed:
```powershell
Test-Path "$toolsDir\poppler\Library\bin\pdftoppm.exe"
```

### If not installed, download and extract:
```powershell
$popplerDir = "$toolsDir\poppler"

# Create .tools folder if needed
if (-not (Test-Path $toolsDir)) { New-Item -ItemType Directory -Path $toolsDir }

# Download latest Poppler for Windows
$popplerUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
$zipPath = "$toolsDir\poppler.zip"

Invoke-WebRequest -Uri $popplerUrl -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $toolsDir -Force

# Find extracted folder (poppler-*) and rename to poppler
$extractedFolder = Get-ChildItem $toolsDir -Directory | Where-Object { $_.Name -like "poppler-*" } | Select-Object -First 1
if ($extractedFolder) { Move-Item $extractedFolder.FullName $popplerDir -ErrorAction SilentlyContinue }

Remove-Item $zipPath -ErrorAction SilentlyContinue
```

### Verify installation:
```powershell
& "$toolsDir\poppler\Library\bin\pdftoppm.exe" -v
```

### Create output folder (tracked in git):
```powershell
$jpgDir = "$toolsDir\poppler_pdf_jpgs"
if (-not (Test-Path $jpgDir)) { New-Item -ItemType Directory -Path $jpgDir }
if (-not (Test-Path "$jpgDir\.gitkeep")) { New-Item -ItemType File -Path "$jpgDir\.gitkeep" }
```

## 4. Install QPDF Locally

QPDF is a command-line tool for PDF transformations (merge, split, encrypt, decrypt, repair).

### Check if already installed:
```powershell
Test-Path "$toolsDir\qpdf\bin\qpdf.exe"
```

### If not installed, download and extract:
```powershell
$qpdfDir = "$toolsDir\qpdf"

# Download latest QPDF for Windows
$qpdfUrl = "https://github.com/qpdf/qpdf/releases/download/v12.3.0/qpdf-12.3.0-msvc64.zip"
$zipPath = "$toolsDir\qpdf.zip"

Invoke-WebRequest -Uri $qpdfUrl -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $toolsDir -Force

# Find extracted folder (qpdf-*) and rename to qpdf
$extractedFolder = Get-ChildItem $toolsDir -Directory | Where-Object { $_.Name -like "qpdf-*" } | Select-Object -First 1
if ($extractedFolder) { Move-Item $extractedFolder.FullName $qpdfDir -ErrorAction SilentlyContinue }

Remove-Item $zipPath -ErrorAction SilentlyContinue
```

### Verify installation:
```powershell
& "$toolsDir\qpdf\bin\qpdf.exe" --version
```

## 5. Install Ghostscript Locally

Ghostscript is used for PDF image compression and downsizing.

### Check if already installed:
```powershell
Test-Path "$toolsDir\gs\bin\gswin64c.exe"
```

### If not installed, download and extract:
```powershell
$gsDir = "$toolsDir\gs"

# Download Ghostscript portable (64-bit)
$gsUrl = "https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10060/gs10060w64.zip"
$zipPath = "$toolsDir\gs.zip"

Invoke-WebRequest -Uri $gsUrl -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $toolsDir -Force

# Find extracted folder (gs*) and rename to gs
$extractedFolder = Get-ChildItem $toolsDir -Directory | Where-Object { $_.Name -like "gs*" -and $_.Name -ne "gs" } | Select-Object -First 1
if ($extractedFolder) { Move-Item $extractedFolder.FullName $gsDir -ErrorAction SilentlyContinue }

Remove-Item $zipPath -ErrorAction SilentlyContinue
```

### Verify installation:
```powershell
& "$toolsDir\gs\bin\gswin64c.exe" --version
```

## 6. Install uv/uvx (Python Package Runner)

uvx runs Python packages without installing them globally. Required for MCP servers.

### Check if already installed:
```powershell
uvx --version
```

### If not installed:
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Installs to `%USERPROFILE%\.local\bin\` (uv.exe, uvx.exe).

### Verify PATH:
After installation, restart terminal or run:
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")
uvx --version
```

## 7. Install Python Dependencies

```powershell
pip install pdf2image Pillow
```

## 8. Final Verification

Test Poppler conversion:
```powershell
& "$toolsDir\poppler\Library\bin\pdftoppm.exe" -jpeg -r 150 "input.pdf" "$toolsDir\poppler_pdf_jpgs\output"
```

## Completion

All tools ready:
- **Python**: Script execution
- **Poppler**: PDF to image conversion (`[WORKSPACE_FOLDER]/.tools/poppler/`)
- **QPDF**: PDF transformations (`[WORKSPACE_FOLDER]/.tools/qpdf/`)
- **Ghostscript**: PDF image compression (`[WORKSPACE_FOLDER]/.tools/gs/`)
- **uv/uvx**: Python package runner for MCP servers
- **Output folder**: `[WORKSPACE_FOLDER]/.tools/poppler_pdf_jpgs/` (tracked via .gitkeep)
