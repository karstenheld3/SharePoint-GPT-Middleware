---
description: update-dependencies
auto_execution_mode: 3
---

1) Run over all .py files and gather the Python packages we need as dpendencies.
2) Clean up the imports in the .py files
  - put all standard Python packages on a single line at the top
  - import everything explicitly from packages; no wildcard imports
  - group all imports from one non-standard packages on single lines, sorted by name
  - examples of non-standard libraries: psutil
  - verify that imports are all listed
  - do not change the order of the imported functions and symbols in a line
  - remove all unneeded imports
3) Read the ./src/pyproject.toml file and update it to contain all packages with pinned version numbers
  - do not chage the order or versions of the packages