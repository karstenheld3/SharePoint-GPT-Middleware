---
description: update-dependencies
auto_execution_mode: 3
---

1) Run over all .py files and gather the Python packages we need as dpendencies.
2) Clean up the imports in the .py files: Remove all unneeded imports and
  - put all standard Python packages on a single line at the top
  - group all imports from one non-standard packages on single lines, sorted by name
  - Examples of non-standard libraries: psutil 
3) Read the ./src/pyproject.toml file and update it to contain all packages with pinned version numbers