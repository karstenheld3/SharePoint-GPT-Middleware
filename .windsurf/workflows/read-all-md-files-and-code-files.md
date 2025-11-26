---
description: Read all md files (except those starting with underscore) and all code files
auto_execution_mode: 3
---

First ask the user which model is used. Make a list with numbers as options. Add "0. Skip - I don't know" at the top.

Context window size (find out which model you are to calculate occupied %):
- Claude 3.5, 3.7, 4, 4.5: 200k
- GPT-5, GPT-5.1: 400k
- Gemini 3: 1000k
- Grok Code Fast 1: 256k, xAi Grok-3: 131k
- Kimi K2: 265k

Make sure you have no duplicates in your read list.
Find all .md files except those starting with underscore in the workspace and all its subfolders.
Find all .md files except those starting with underscore in [workspace]/.windsurf and all its subfolders.
Read these files.

Then read all .py files in the workspace including those in subfolders.

Return only a single line: "Model: '[Model Name]' read [x] md files, [y] code files, [z]k context tokens (??%) occupied"