---
trigger: always_on
---

# Tools Rules

Rules and usage for PDF tools in `[WORKSPACE_FOLDER]/.tools/`.

## PDF to JPG Conversion

### Script: `.tools/convert-pdf-to-jpg.py`

Converts PDF pages to JPG images for vision analysis.

**Usage:**
```powershell
python .tools/convert-pdf-to-jpg.py <input.pdf> [--output-dir <dir>] [--dpi <dpi>] [--pages <range>]
```

**Examples:**
```powershell
python .tools/convert-pdf-to-jpg.py invoice.pdf
python .tools/convert-pdf-to-jpg.py invoice.pdf --dpi 200 --pages 1-2
python .tools/convert-pdf-to-jpg.py invoice.pdf --pages 1
```

**Output Convention:**
- Default output: `.tools/poppler_pdf_jpgs/[PDF_FILENAME]/`
- Each PDF gets its own subfolder named after the PDF file (without extension)
- Files named: `[PDF_FILENAME]_page001.jpg`, `[PDF_FILENAME]_page002.jpg`, etc.
- Check for existing subfolder to skip re-conversion

**Parameters:**
- `--output-dir, -o`: Output directory (default: `.tools/poppler_pdf_jpgs/`)
- `--dpi, -d`: Resolution (default: 150)
- `--pages, -p`: Page range - "1", "1-3", or "all" (default: all)

## Poppler CLI Tools

Location: `.tools/poppler/Library/bin/`

### pdftoppm - PDF to Image
```powershell
& ".tools\poppler\Library\bin\pdftoppm.exe" -jpeg -r 150 "input.pdf" "output_prefix"
```

### pdftotext - Extract Text
```powershell
& ".tools\poppler\Library\bin\pdftotext.exe" "input.pdf" "output.txt"
```

### pdfinfo - Get PDF Metadata
```powershell
& ".tools\poppler\Library\bin\pdfinfo.exe" "input.pdf"
```

### pdfseparate - Split PDF Pages
```powershell
& ".tools\poppler\Library\bin\pdfseparate.exe" "input.pdf" "output_%d.pdf"
```

### pdfunite - Merge PDFs
```powershell
& ".tools\poppler\Library\bin\pdfunite.exe" "page1.pdf" "page2.pdf" "merged.pdf"
```

## QPDF CLI Tools

Location: `.tools/qpdf/bin/`

### Merge PDFs
```powershell
& ".tools\qpdf\bin\qpdf.exe" --empty --pages file1.pdf file2.pdf -- merged.pdf
```

### Split PDF (extract pages)
```powershell
& ".tools\qpdf\bin\qpdf.exe" input.pdf --pages . 1-5 -- output.pdf
```

### Decrypt PDF
```powershell
& ".tools\qpdf\bin\qpdf.exe" --decrypt --password=secret encrypted.pdf decrypted.pdf
```

### Repair PDF
```powershell
& ".tools\qpdf\bin\qpdf.exe" --replace-input damaged.pdf
```

### Linearize (optimize for web)
```powershell
& ".tools\qpdf\bin\qpdf.exe" --linearize input.pdf output.pdf
```

## Ghostscript CLI Tools

Location: `.tools/gs/bin/`

### Compress images (downsize PDF)
```powershell
& ".tools\gs\bin\gswin64c.exe" -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen -dDownsampleColorImages=true -dColorImageResolution=72 -dDownsampleGrayImages=true -dGrayImageResolution=72 -dDownsampleMonoImages=true -dMonoImageResolution=72 -dNOPAUSE -dQUIET -dBATCH -sOutputFile=output.pdf input.pdf
```

### Quality presets (`-dPDFSETTINGS`)
- `/screen` - 72 DPI, smallest file size
- `/ebook` - 150 DPI, medium quality
- `/printer` - 300 DPI, high quality
- `/prepress` - 300 DPI, color preserving

### Remove all images (text only)
```powershell
& ".tools\gs\bin\gswin64c.exe" -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dFILTERIMAGE=true -dNOPAUSE -dQUIET -dBATCH -sOutputFile=output.pdf input.pdf
```

## PDF Downsizing Workflow

Two-pass workflow for maximum compression:

### Pass 1: Ghostscript (image compression)
```powershell
& ".tools\gs\bin\gswin64c.exe" -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen -dDownsampleColorImages=true -dColorImageResolution=72 -dDownsampleGrayImages=true -dGrayImageResolution=72 -dNOPAUSE -dQUIET -dBATCH -sOutputFile=temp.pdf input.pdf
```

### Pass 2: QPDF (structure optimization)
```powershell
& ".tools\qpdf\bin\qpdf.exe" --linearize --object-streams=generate --stream-data=compress --compress-streams=y --optimize-images --flatten-annotations=screen temp.pdf output.pdf
Remove-Item temp.pdf
```

## Best Practices

1. **Check existing conversions**: Before converting, check if subfolder exists in `poppler_pdf_jpgs/`
2. **Use appropriate DPI**: 150 DPI for screen viewing, 300 DPI for OCR
3. **Convert specific pages**: Use `--pages` to avoid converting entire large PDFs
4. **Clean up**: Delete old conversions when no longer needed
5. **Two-pass downsizing**: Use Ghostscript first (images), then QPDF (structure) for best compression
