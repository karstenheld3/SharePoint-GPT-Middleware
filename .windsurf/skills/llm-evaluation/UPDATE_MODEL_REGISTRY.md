# Update Model Registry Workflow

**Goal**: Capture model overview pages, transcribe to markdown, and update `model-registry.json` with current models, context windows, and deprecation status

## Placeholders

- `[SKILL_FOLDER]`: The folder containing this workflow file (e.g., `.windsurf/skills/llm-evaluation`)
- `[REGISTRY_SOURCES]`: `[SKILL_FOLDER]/registry-sources`
- `[SCREENSHOTS]`: `[WORKSPACE_FOLDER]/../.tools/_screenshots`
- `[DATE]`: Current date in `YYYY-MM-DD` format
- `[VENV_PYTHON]`: Path to the llm-transcription venv Python (e.g., `../.tools/llm-venv/Scripts/python.exe`)
- `[TRANSCRIPTION_SCRIPT]`: Path to `transcribe-image-to-markdown.py` in the llm-transcription skill folder
- `[KEYS_FILE]`: Path to API keys file

## Sources

- Anthropic Models Overview: `https://platform.claude.com/docs/en/about-claude/models/overview`
- Anthropic Model Deprecations: `https://platform.claude.com/docs/en/about-claude/model-deprecations`
- OpenAI Model Compare: `https://platform.openai.com/docs/models/compare`

## Step 1: Capture Model Info Screenshots

Use the **Playwright MCP** tools to capture screenshots. Each source gets its own subfolder under `[SCREENSHOTS]`:

- `[SCREENSHOTS]/[DATE]_Anthropic-ModelOverview/`
- `[SCREENSHOTS]/[DATE]_Anthropic-ModelDeprecations/`
- `[SCREENSHOTS]/[DATE]_OpenAI-ModelCompare/`

Create these folders before capturing.

### Common Steps (all pages)

For each page:

1. `browser_navigate(url: "<URL>")`
2. `browser_wait_for(time: 2)`
3. **Dismiss cookie popup** (see `@ms-playwright-mcp` PLAYWRIGHT_ADVANCED_WORKFLOWS.md Section 1):
   - `browser_snapshot()` - Check for cookie consent banner
   - Click "Accept" / "Accept All Cookies" button if found
   - If no button, use JavaScript removal fallback:
     ```
     browser_evaluate(function: "(() => {
       ['#cookie-banner','#cookieModal','.cookie-consent','[class*=\"cookie\"]',
        '[id*=\"cookie\"]','.gdpr-banner','#onetrust-consent-sdk'].forEach(sel =>
         document.querySelectorAll(sel).forEach(el => el.remove()));
       document.querySelectorAll('.modal-backdrop,[class*=\"overlay\"]').forEach(el => el.remove());
       document.body.style.overflow = 'auto';
     })()")
     ```
4. Remove fixed/sticky headers:
   ```
   browser_evaluate(function: "() => {
     document.querySelectorAll('header, nav, [class*=\"sticky\"], [class*=\"fixed\"]')
       .forEach(el => { el.style.position = 'relative'; });
   }")
   ```

### 1a. Capture Anthropic Models Overview

URL: `https://platform.claude.com/docs/en/about-claude/models/overview`

The Anthropic docs pages use the document body for scrolling. Use viewport-chunk capture:

```
browser_run_code(code: "async (page) => {
  await page.evaluate(async () => {
    const delay = ms => new Promise(r => setTimeout(r, ms));
    let prevHeight = -1;
    for (let i = 0; i < 50; i++) {
      window.scrollBy(0, 500); await delay(300);
      if (document.body.scrollHeight === prevHeight) break;
      prevHeight = document.body.scrollHeight;
    }
    window.scrollTo(0, 0);
    document.querySelectorAll('header, nav, [class*=\"sticky\"], [class*=\"fixed\"]')
      .forEach(el => { el.style.position = 'relative'; });
  });
  const totalHeight = await page.evaluate(() => document.body.scrollHeight);
  const viewportHeight = await page.evaluate(() => window.innerHeight);
  const pages = Math.ceil(totalHeight / viewportHeight);
  for (let i = 0; i < pages; i++) {
    await page.evaluate(y => window.scrollTo(0, y), i * viewportHeight);
    await page.waitForTimeout(500);
    const suffix = String(i + 1).padStart(2, '0');
    await page.screenshot({
      path: '[SUBFOLDER]/' + suffix + '.jpg',
      scale: 'css', type: 'jpeg', quality: 90
    });
  }
  return { pages };
}")
```

Replace `[SUBFOLDER]` with: `[SCREENSHOTS]/[DATE]_Anthropic-ModelOverview`

### 1b. Capture Anthropic Model Deprecations

URL: `https://platform.claude.com/docs/en/about-claude/model-deprecations`

Same viewport-chunk technique as 1a. Replace `[SUBFOLDER]` with: `[SCREENSHOTS]/[DATE]_Anthropic-ModelDeprecations`

### 1c. Capture OpenAI Model Compare

URL: `https://platform.openai.com/docs/models/compare`

**IMPORTANT**: This page shows a comparison table for up to 3 models at a time. To capture all models, use an interactive loop:

**IMPORTANT**: The OpenAI docs pages use a scrollable inner container (`div.docs-scroll-container`), not the document body. Use inner-container scrolling for all interactions.

#### Step 1c-i: Get full model list

```
browser_run_code(code: "async (page) => {
  // Click first model selector to open dropdown
  const selectors = await page.locator('[data-testid=\"model-selector\"], button:has-text(\"Select a model\"), .model-picker button').all();
  if (selectors.length > 0) await selectors[0].click();
  await page.waitForTimeout(500);
  // Extract all model names from dropdown
  const models = await page.evaluate(() => {
    const items = document.querySelectorAll('[role=\"option\"], [role=\"menuitem\"], .model-option, li[data-value]');
    return Array.from(items).map(el => el.textContent.trim());
  });
  return { models, count: models.length };
}")
```

If the above selectors don't match, use `browser_snapshot()` to inspect the page structure and adapt.

#### Step 1c-ii: Capture in batches of 3

The compare page supports exactly 3 model slots. For N models, you need `ceil(N / 3)` batches.

For each batch:

1. **Select 3 models** in the comparison slots using the dropdown/selector UI
2. **Wait** for the comparison table to load
3. **Scroll** the inner container to capture the full comparison table
4. **Screenshot** as viewport chunks with batch prefix

```
browser_run_code(code: "async (page) => {
  // After selecting models for this batch, scroll and capture
  const container = await page.evaluate(async () => {
    const c = document.querySelector('.docs-scroll-container');
    const delay = ms => new Promise(r => setTimeout(r, ms));
    let prevHeight = -1;
    for (let i = 0; i < 50; i++) {
      c.scrollBy(0, 500); await delay(300);
      if (c.scrollHeight === prevHeight) break;
      prevHeight = c.scrollHeight;
    }
    c.scrollTo(0, 0);
    document.querySelectorAll('header, nav, [class*=\"sticky\"], [class*=\"fixed\"]')
      .forEach(el => { el.style.position = 'relative'; });
    return { totalHeight: c.scrollHeight, viewportHeight: c.clientHeight };
  });
  const pages = Math.ceil(container.totalHeight / container.viewportHeight);
  for (let i = 0; i < pages; i++) {
    await page.evaluate(idx => {
      const c = document.querySelector('.docs-scroll-container');
      c.scrollTo(0, idx * c.clientHeight);
    }, i);
    await page.waitForTimeout(500);
    const suffix = 'B[BATCH_NUM]_' + String(i + 1).padStart(2, '0');
    await page.screenshot({
      path: '[SUBFOLDER]/' + suffix + '.jpg',
      scale: 'css', type: 'jpeg', quality: 90
    });
  }
  return { pages };
}")
```

Replace `[SUBFOLDER]` with: `[SCREENSHOTS]/[DATE]_OpenAI-ModelCompare`
Replace `[BATCH_NUM]` with the zero-padded batch number (01, 02, 03, ...).

**Naming convention**: Files are named `B01_01.jpg`, `B01_02.jpg`, `B02_01.jpg`, etc. (batch + page within batch). This ensures correct sort order during stitching.

**Note**: The exact UI for selecting models may change. Use `browser_snapshot()` before each batch to identify the correct selectors. The agent should adapt to the current page structure.

## Step 2: Transcribe Screenshots to Markdown

### 2a. Transcribe Anthropic Model Overview

```powershell
& [VENV_PYTHON] [TRANSCRIPTION_SCRIPT] `
  --input-folder "[SCREENSHOTS]/[DATE]_Anthropic-ModelOverview" `
  --output-folder "[SCREENSHOTS]/[DATE]_Anthropic-ModelOverview" `
  --model gpt-5-mini `
  --initial-candidates 1 `
  --keys-file [KEYS_FILE] `
  --force
```

### 2b. Transcribe Anthropic Deprecations

```powershell
& [VENV_PYTHON] [TRANSCRIPTION_SCRIPT] `
  --input-folder "[SCREENSHOTS]/[DATE]_Anthropic-ModelDeprecations" `
  --output-folder "[SCREENSHOTS]/[DATE]_Anthropic-ModelDeprecations" `
  --model gpt-5-mini `
  --initial-candidates 1 `
  --keys-file [KEYS_FILE] `
  --force
```

### 2c. Transcribe OpenAI Model Compare

```powershell
& [VENV_PYTHON] [TRANSCRIPTION_SCRIPT] `
  --input-folder "[SCREENSHOTS]/[DATE]_OpenAI-ModelCompare" `
  --output-folder "[SCREENSHOTS]/[DATE]_OpenAI-ModelCompare" `
  --model gpt-5-mini `
  --initial-candidates 1 `
  --keys-file [KEYS_FILE] `
  --force
```

### 2d. Stitch Page Transcriptions into Combined Markdowns

Concatenate in sort order into single combined files at `[REGISTRY_SOURCES]`:

```powershell
# Anthropic Models Overview
Get-ChildItem "[SCREENSHOTS]/[DATE]_Anthropic-ModelOverview/*.md" |
  Sort-Object Name |
  ForEach-Object { Get-Content $_.FullName -Raw } |
  Out-File "[REGISTRY_SOURCES]/[DATE]_Anthropic-ModelOverview.md" -Encoding utf8

# Anthropic Deprecations
Get-ChildItem "[SCREENSHOTS]/[DATE]_Anthropic-ModelDeprecations/*.md" |
  Sort-Object Name |
  ForEach-Object { Get-Content $_.FullName -Raw } |
  Out-File "[REGISTRY_SOURCES]/[DATE]_Anthropic-ModelDeprecations.md" -Encoding utf8

# OpenAI Model Compare (batch files sort correctly: B01_01, B01_02, B02_01, ...)
Get-ChildItem "[SCREENSHOTS]/[DATE]_OpenAI-ModelCompare/*.md" |
  Sort-Object Name |
  ForEach-Object { Get-Content $_.FullName -Raw } |
  Out-File "[REGISTRY_SOURCES]/[DATE]_OpenAI-ModelCompare.md" -Encoding utf8
```

Clean up individual page .md files and batch summaries from screenshot subfolders:

```powershell
"Anthropic-ModelOverview", "Anthropic-ModelDeprecations", "OpenAI-ModelCompare" | ForEach-Object {
  Remove-Item "[SCREENSHOTS]/[DATE]_$_/*.md" -Force -ErrorAction SilentlyContinue
  Remove-Item "[SCREENSHOTS]/[DATE]_$_/_batch_summary.json" -Force -ErrorAction SilentlyContinue
}
```

**Expected output files:**
- `[REGISTRY_SOURCES]/[DATE]_Anthropic-ModelOverview.md`
- `[REGISTRY_SOURCES]/[DATE]_Anthropic-ModelDeprecations.md`
- `[REGISTRY_SOURCES]/[DATE]_OpenAI-ModelCompare.md`

## Step 3: Read Transcriptions and Update model-registry.json

### 3a. Read Combined Markdown Files

Read all three combined transcription files from `[REGISTRY_SOURCES]`.

### 3b. Extract Model Data

From the transcribed markdown, extract for each model:
- **Model ID** (API identifier)
- **Provider** (`openai` or `anthropic`)
- **Display name**
- **Context window** (max input tokens)
- **Max output tokens**
- **Deprecation status** and dates (from the deprecations page)

**Rules:**
- Use the full API model ID for Anthropic (with date suffix)
- Use the short model name for OpenAI (e.g., `gpt-5-mini`, not a dated version)
- Context window values are typically stated as "200K context" meaning 200,000 tokens

### 3c. Update model-registry.json `models[]`

Read the existing `[SKILL_FOLDER]/model-registry.json` and update the `models` array:

1. **Add** new models not yet present with `"enabled": false, "status": "untested"`
2. **Update** `context_window` for existing models if now known
3. **Update** `status` to `"deprecated"` and set `"enabled": false` for models listed on the deprecation page
4. **NEVER remove** existing models - they may still be referenced by evaluation results
5. Insert new models at the top of their provider group, newest first

### 3d. Update model-registry.json `model_id_startswith[]`

1. **Update** `max_input` for existing prefix entries based on context window data
2. Check if any new model fails to match an existing prefix - if so, **report** it (do NOT auto-add prefix entries, they require manual API behavior configuration)

### 3e. Update Metadata

- Update `_updated` to today's `[DATE]`
- Bump `_version` patch number (e.g., `1.1.0` -> `1.1.1`)

### 3f. Verify

After updating, verify:
- JSON is valid (no syntax errors)
- All `context_window` values are positive integers
- All `max_input` values are positive integers
- No duplicate model entries in `models[]`
- No duplicate prefixes in `model_id_startswith[]`
- Every model in `models[]` matches at least one `model_id_startswith` prefix
- `_updated` matches today's date

## Step 4: Report Changes

Summarize what changed:
- Models added to `models[]` (with context window and status)
- Models with updated context windows (old vs new)
- Models newly marked as deprecated
- New `max_input` values added to `model_id_startswith[]`
- Any models found in screenshots that don't match a `model_id_startswith` prefix (requires manual config)
- Any models skipped (with reason)

## Notes

- The OpenAI compare page UI may change. Always use `browser_snapshot()` to inspect the current structure before interacting with model selectors.
- The Anthropic models overview page lists context window and max output per model family. Map these to specific model IDs using the date-suffixed IDs from the pricing or deprecation pages.
- If a model appears on both the overview and deprecation pages, the deprecation page takes precedence for status.
- The `model_id_startswith` section uses prefix matching with longest-prefix-wins ordering. More specific prefixes must appear before general ones.
