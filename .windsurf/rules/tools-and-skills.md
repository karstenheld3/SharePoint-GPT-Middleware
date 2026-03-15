---
trigger: always_on
---

# Tools and Skills

Tool-specific knowledge and disambiguation.

## Browser Automation (Playwright vs Playwriter)

**These are different tools with confusingly similar names:**

- **Playwright MCP** (default) - Microsoft's MCP server. Spawns fresh browser instance. `npx @playwright/mcp@latest`
- **Playwriter** (exception) - Chrome extension + CLI. Uses your **real browser** with existing logins/cookies. Install from `playwriter.dev`

**When to use:**
- **Playwright MCP**: Default choice. Clean sessions, standard automation, no existing auth needed
- **Playwriter**: When explicity asked for by user using `Playwriter` term
