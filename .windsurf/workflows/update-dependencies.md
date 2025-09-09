---
description: update-dependencies
auto_execution_mode: 3
---

1) Run over all .py files and gather the Python packages we need as dpendencies.
2) Clean up the imports in the .py files: Remove all unneeded imports and make the imports single line (group common)
3) Read the ./src/pyproject.toml file and update it to contain all packages with pinned version numbers