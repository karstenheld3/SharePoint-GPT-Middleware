# Setup UI Testing with Playwright MCP

Sets up the Playwright MCP server for browser automation and UI testing with Claude Code.

## Overview

This workflow configures the Playwright MCP server which enables:
- Browser automation (Chrome, Firefox, WebKit)
- Screenshot capture and visual validation
- Form interaction and validation testing
- Accessibility testing via semantic page analysis
- End-to-end UI flow testing

## Prerequisites

1. Node.js installed (v18+ recommended)
2. Claude Code CLI installed and configured
3. npm/npx available in PATH

## Workflow Steps

### Step 1: Check Current MCP Configuration

**1.1 List existing MCP servers:**
```bash
claude mcp list
```

**1.2 Check if Playwright is already configured:**
- Look for `playwright` in the output
- If present, skip to Step 4 (Verification)

### Step 2: Install Playwright MCP Server

**2.1 Add Playwright MCP with project scope (recommended for team sharing):**
```bash
claude mcp add playwright --scope project -- npx -y @anthropic-ai/mcp-playwright
```

**Alternative scopes:**
- `--scope local` - Only for this machine, not shared
- `--scope user` - Available in all your projects
- `--scope project` - Shared via `.mcp.json` (recommended for teams)

**2.2 Verify the command succeeded:**
```bash
claude mcp list
```

Expected output should include:
```
playwright: npx -y @anthropic-ai/mcp-playwright (project)
```

### Step 3: Install Browser Dependencies

**3.1 Install Playwright browsers:**
```bash
npx playwright install
```

This installs Chromium, Firefox, and WebKit browsers.

**3.2 For minimal installation (Chromium only):**
```bash
npx playwright install chromium
```

**3.3 Verify browser installation:**
```bash
npx playwright --version
```

### Step 4: Verify MCP Server Works

**4.1 Start a Claude Code session:**
```bash
claude
```

**4.2 Test basic browser automation:**
Ask Claude to perform these verification tests:

```
Test 1: Navigate to a URL
> Navigate to https://example.com and describe what you see

Test 2: Take a screenshot
> Take a screenshot of the current page

Test 3: Interact with elements
> Click on the "More information..." link on example.com

Test 4: Check accessibility
> List all interactive elements on the page
```

**4.3 Expected behavior:**
- Claude should be able to launch a browser
- Navigate to URLs
- Capture screenshots
- Click elements and fill forms
- Read page content via accessibility tree

### Step 5: Configure for This Project

**5.1 Create project-specific test configuration:**

Create `.claude/ui-test-config.json`:
```json
{
  "baseUrl": "http://127.0.0.1:8000",
  "browser": "chromium",
  "headless": true,
  "timeout": 30000,
  "viewport": {
    "width": 1280,
    "height": 720
  },
  "testPages": [
    "/docs",
    "/redoc",
    "/v2/domains",
    "/v2/jobs"
  ]
}
```

**5.2 Add environment variables (optional):**
```bash
claude mcp add playwright --scope project \
  --env HEADLESS=true \
  --env SLOWMO=0 \
  -- npx -y @anthropic-ai/mcp-playwright
```

### Step 6: Create UI Test Workflow

**6.1 Verify `.mcp.json` was created:**
```bash
cat .mcp.json
```

Expected content:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-playwright"]
    }
  }
}
```

**6.2 Add `.mcp.json` to version control:**
```bash
git add .mcp.json
git commit -m "Add Playwright MCP for UI testing"
```

## Troubleshooting

### Issue: "MCP server failed to start"

**Cause:** Node.js or npx not in PATH, or package not found.

**Fix:**
```bash
# Verify Node.js
node --version  # Should be v18+

# Clear npm cache and retry
npm cache clean --force
claude mcp remove playwright
claude mcp add playwright -- npx -y @anthropic-ai/mcp-playwright
```

### Issue: "Browser launch failed"

**Cause:** Playwright browsers not installed or missing dependencies.

**Fix:**
```bash
# Install browsers with dependencies
npx playwright install --with-deps

# Or install system dependencies manually (Linux)
npx playwright install-deps
```

### Issue: "Timeout waiting for browser"

**Cause:** Slow system or network issues.

**Fix:** Increase timeout in MCP configuration:
```bash
claude mcp add playwright \
  --env PLAYWRIGHT_TIMEOUT=60000 \
  -- npx -y @anthropic-ai/mcp-playwright
```

### Issue: "Cannot find element"

**Cause:** Page not fully loaded or element not visible.

**Fix:** In your Claude prompts, be explicit:
```
> Wait for the page to fully load, then click the submit button
> Wait for the element with text "Login" to be visible before clicking
```

### Issue: "Permission denied" on Windows

**Cause:** PowerShell execution policy.

**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Usage Examples

### Example 1: Test API Documentation UI

```
> Navigate to http://127.0.0.1:8000/docs
> Verify the Swagger UI loads correctly
> Expand the /v2/domains section
> Take a screenshot of the available endpoints
```

### Example 2: Test Form Validation

```
> Navigate to http://127.0.0.1:8000/docs
> Find the POST /v2/domains/create endpoint
> Click "Try it out"
> Submit without filling required fields
> Verify validation error messages appear
> Take a screenshot of the error state
```

### Example 3: End-to-End Flow

```
> Navigate to http://127.0.0.1:8000/docs
> Test the complete domain creation flow:
>   1. POST /v2/domains/create with domain_id="test_domain"
>   2. GET /v2/domains/get to verify it was created
>   3. DELETE /v2/domains/delete to clean up
> Report any errors encountered
```

### Example 4: Visual Regression

```
> Navigate to http://127.0.0.1:8000/docs
> Take screenshots at these viewports:
>   - Desktop (1920x1080)
>   - Tablet (768x1024)
>   - Mobile (375x667)
> Compare the layouts and report any issues
```

### Example 5: Accessibility Testing

```
> Navigate to http://127.0.0.1:8000/docs
> Check accessibility:
>   - Are all form fields properly labeled?
>   - Is keyboard navigation working?
>   - Are there any color contrast issues?
> Generate an accessibility report
```

## Integration with /run-tests

After setup, you can create a combined test workflow:

```bash
# Run API tests first
/run-tests

# Then run UI tests
/run-ui-tests
```

## Security Considerations

1. **Test Environments Only**: Only use UI testing against test/dev environments
2. **No Production Credentials**: Never use real user credentials in automated tests
3. **Headless Mode**: Use `HEADLESS=true` in CI/CD pipelines
4. **Network Isolation**: Consider running tests in isolated network environments

## Quality Criteria

Setup is complete when:
1. `claude mcp list` shows playwright server
2. Claude can navigate to URLs in a browser
3. Claude can take screenshots
4. Claude can interact with page elements
5. `.mcp.json` is committed to version control (if using project scope)

## Next Steps

After successful setup:
1. Create `/run-ui-tests` command for automated UI test execution
2. Add UI tests to CI/CD pipeline
3. Set up visual regression baseline screenshots
4. Document project-specific UI test cases
