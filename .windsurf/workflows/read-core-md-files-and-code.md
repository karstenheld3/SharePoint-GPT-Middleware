---
description: Read core md files (except those starting with underscore) and core code files
auto_execution_mode: 3
---

Make sure you have no duplicates in your read list.
Find all .md files except those starting with underscore in the workspace and all its subfolders.
Find all .md files except those starting with underscore in [workspace]/.windsurf and all its subfolders.
Read these files.

Then read:
- /src: app.py, utils.py
- /src/routers: crawler.py, domains.py, inventory.py

Return only a single line: "Read [x] md files, [y] code files, [z]k context tokens"