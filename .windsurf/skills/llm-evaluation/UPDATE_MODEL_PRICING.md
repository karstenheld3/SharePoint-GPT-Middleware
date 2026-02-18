# Update Model Pricing Workflow

**Goal**: Capture current pricing pages, transcribe to markdown, and update `model-pricing.json`

## Placeholders

- `[SKILL_FOLDER]`: The folder containing this workflow file (e.g., `.windsurf/skills/llm-evaluation`)
- `[PRICING_SOURCES]`: `[SKILL_FOLDER]/pricing-sources`
- `[SCREENSHOTS]`: `[WORKSPACE_FOLDER]/../.tools/_screenshots`
- `[DATE]`: Current date in `YYYY-MM-DD` format
- `[VENV_PYTHON]`: Path to the llm-transcription venv Python (e.g., `../.tools/llm-venv/Scripts/python.exe`)
- `[TRANSCRIPTION_SCRIPT]`: Path to `transcribe-image-to-markdown.py` in the llm-transcription skill folder
- `[KEYS_FILE]`: Path to API keys file

## Sources

- Anthropic: `https://docs.anthropic.com/en/docs/about-claude/pricing`
- OpenAI: `https://platform.openai.com/docs/pricing`

## Step 1: Capture Pricing Page Screenshots

Use the **Playwright MCP** tools to capture viewport-sized screenshot chunks of both pricing pages. Each provider gets its own subfolder under `[SCREENSHOTS]`:

- `[SCREENSHOTS]/[DATE]_Anthropic-ModelPricing/` - Anthropic screenshots
- `[SCREENSHOTS]/[DATE]_OpenAI-ModelPricing/` - OpenAI screenshots

Create these folders before capturing.

### Common Steps (both providers)

For each pricing page:

1. `browser_navigate(url: "<pricing URL>")`
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
5. Determine scrollable container and take viewport-chunk screenshots (see provider-specific sections below)

### 1a. Capture Anthropic Pricing

URL: `https://docs.anthropic.com/en/docs/about-claude/pricing`

The Anthropic page uses the document body for scrolling. Scroll to load lazy content, then take viewport chunks:

```
browser_run_code(code: "async (page) => {
  // Scroll to load lazy content
  await page.evaluate(async () => {
    const delay = ms => new Promise(r => setTimeout(r, ms));
    let prevHeight = -1;
    for (let i = 0; i < 50; i++) {
      window.scrollBy(0, 500); await delay(300);
      if (document.body.scrollHeight === prevHeight) break;
      prevHeight = document.body.scrollHeight;
    }
    window.scrollTo(0, 0);
    // Remove sticky headers
    document.querySelectorAll('header, nav, [class*=\"sticky\"], [class*=\"fixed\"]')
      .forEach(el => { el.style.position = 'relative'; });
  });
  // Take viewport-chunk screenshots
  const totalHeight = await page.evaluate(() => document.body.scrollHeight);
  const viewportHeight = await page.evaluate(() => window.innerHeight);
  const pages = Math.ceil(totalHeight / viewportHeight);
  for (let i = 0; i < pages; i++) {
    await page.evaluate(y => window.scrollTo(0, y), i * viewportHeight);
    await page.waitForTimeout(500);
    const suffix = String(i + 1).padStart(2, '0');
    await page.screenshot({
      path: '[SUBFOLDER_ANTHROPIC]/' + suffix + '.jpg',
      scale: 'css', type: 'jpeg', quality: 90
    });
  }
  return { pages };
}")
```

Replace `[SUBFOLDER_ANTHROPIC]` with the actual path: `[SCREENSHOTS]/[DATE]_Anthropic-ModelPricing`

### 1b. Capture OpenAI Pricing

URL: `https://platform.openai.com/docs/pricing`

**IMPORTANT**: The OpenAI page uses a scrollable inner container (`div.docs-scroll-container`), not the document body. `fullPage: true` will NOT capture the full content. Scroll the inner container instead:

```
browser_run_code(code: "async (page) => {
  // Scroll inner container to load lazy content
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
    // Remove sticky headers
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
    const suffix = String(i + 1).padStart(2, '0');
    await page.screenshot({
      path: '[SUBFOLDER_OPENAI]/' + suffix + '.jpg',
      scale: 'css', type: 'jpeg', quality: 90
    });
  }
  return { pages };
}")
```

Replace `[SUBFOLDER_OPENAI]` with the actual path: `[SCREENSHOTS]/[DATE]_OpenAI-ModelPricing`

## Step 2: Transcribe Screenshots to Markdown

Use the `transcribe-image-to-markdown.py` script from the llm-transcription skill. Since each provider's screenshots are in their own subfolder, use `--input-folder` to transcribe all images in that folder at once. The output markdown files are placed in the same subfolder.

### 2a. Transcribe Anthropic Screenshots

```powershell
& [VENV_PYTHON] [TRANSCRIPTION_SCRIPT] `
  --input-folder "[SCREENSHOTS]/[DATE]_Anthropic-ModelPricing" `
  --output-folder "[SCREENSHOTS]/[DATE]_Anthropic-ModelPricing" `
  --model gpt-5-mini `
  --initial-candidates 1 `
  --keys-file [KEYS_FILE] `
  --force
```

### 2b. Transcribe OpenAI Screenshots

```powershell
& [VENV_PYTHON] [TRANSCRIPTION_SCRIPT] `
  --input-folder "[SCREENSHOTS]/[DATE]_OpenAI-ModelPricing" `
  --output-folder "[SCREENSHOTS]/[DATE]_OpenAI-ModelPricing" `
  --model gpt-5-mini `
  --initial-candidates 1 `
  --keys-file [KEYS_FILE] `
  --force
```

### 2c. Stitch Page Transcriptions into Combined Markdowns

The transcription tool produces one .md per screenshot. Concatenate them in sort order into single combined files at the `[PRICING_SOURCES]` level, then clean up:

```powershell
# Anthropic
Get-ChildItem "[SCREENSHOTS]/[DATE]_Anthropic-ModelPricing/*.md" |
  Sort-Object Name |
  ForEach-Object { Get-Content $_.FullName -Raw } |
  Out-File "[PRICING_SOURCES]/[DATE]_Anthropic-ModelPricing.md" -Encoding utf8

# OpenAI
Get-ChildItem "[SCREENSHOTS]/[DATE]_OpenAI-ModelPricing/*.md" |
  Sort-Object Name |
  ForEach-Object { Get-Content $_.FullName -Raw } |
  Out-File "[PRICING_SOURCES]/[DATE]_OpenAI-ModelPricing-Standard.md" -Encoding utf8
```

Delete individual page .md files and batch summary from screenshot subfolders (keep JPGs as archival reference):

```powershell
Remove-Item "[SCREENSHOTS]/[DATE]_Anthropic-ModelPricing/*.md" -Force
Remove-Item "[SCREENSHOTS]/[DATE]_Anthropic-ModelPricing/_batch_summary.json" -Force
Remove-Item "[SCREENSHOTS]/[DATE]_OpenAI-ModelPricing/*.md" -Force
Remove-Item "[SCREENSHOTS]/[DATE]_OpenAI-ModelPricing/_batch_summary.json" -Force
```

**Expected output files:**
- `[PRICING_SOURCES]/[DATE]_Anthropic-ModelPricing.md`
- `[PRICING_SOURCES]/[DATE]_OpenAI-ModelPricing-Standard.md`

## Step 3: Read Transcriptions and Update model-pricing.json

### 3a. Read Combined Markdown Files

Read the two combined transcription files from `[PRICING_SOURCES]`:
- `[DATE]_Anthropic-ModelPricing.md`
- `[DATE]_OpenAI-ModelPricing-Standard.md`

### 3b. Extract Pricing Data

From the transcribed markdown, extract for each model:
- **Model ID** (API identifier, e.g., `claude-opus-4-6-20260204`, `gpt-5.2`)
- **Input price per 1M tokens**
- **Output price per 1M tokens**

**Rules:**
- Use the full API model ID for Anthropic (with date suffix)
- Use the short model name for OpenAI (e.g., `gpt-5-mini`, not a dated version)
- Only include models that have clear per-token pricing (skip batch-only or special pricing tiers)
- Currency is always `USD`

### 3c. Update model-pricing.json

Read the existing `[SKILL_FOLDER]/model-pricing.json` and update:

1. **Add** new models not yet present (insert at top of their provider section, newest first)
2. **Update** prices for existing models if they changed
3. **NEVER remove** existing models - they may be legacy but still valid for cost calculation
4. **Update** `last_updated` to today's `[DATE]` (YYYY-MM-DD)
5. **Update** `sources` URLs if they changed
6. Maintain the existing JSON structure and formatting

**CRITICAL:** Always update `last_updated`. Always keep all existing models.

### 3d. Verify

After updating, verify:
- JSON is valid (no syntax errors)
- All prices are positive numbers
- No duplicate model entries
- `last_updated` matches today's date

## Step 4: Report Changes

Summarize what changed:
- Models added (with prices)
- Models with price changes (old vs new)
- Models unchanged
- Any models found in screenshots but skipped (with reason)

## Notes

- Screenshots may span multiple pages/images. Read ALL numbered files for a source before extracting prices.
- The OpenAI pricing page may have separate sections for standard and batch pricing. Only extract **standard** (non-batch) pricing.
- If a model has different pricing tiers (e.g., long context), use the **standard** tier pricing.
- The Anthropic pricing page uses full model IDs with date suffixes. Always use the full ID as it appears in the API.
