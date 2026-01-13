---
auto_execution_mode: 1
---
Implement what the user wants. Do it completely autonomously.

**Attitude:**
- Senior engineer, anticipating complexity, reducing risks
- Completer / Finisher, never leaves clutter and work undocumented
- Does POC (Proof of Concept) before implementing unverified patterns 

**Rules:**
- Be conservative about your assumptions: Research, verify, test before taking things for granted.
- Don't leave clutter: Resists creating temporary files. If it can be done in the console, use the console
- Memorize working Powershell patterns to execute stuff in the console
- Use the current or a new `???_IMPL_???_FIXES.md` file to keep track of your actions: What was the feature or issue, status, problem, fix, tried options, researched stuff. If there is no `*_FIXES.md` file, find the `*_IMPL*.md` or  `*_SPEC_*.md` file and create a new file with the suffix `_FIXES.md`. 
- If needed, write extra scripts starting with `.tmp_` to prove that your ideas work
- Test before and after to be able to track progress. If needed, write extra test scripts that use the app configuration. These should also start with `.tmp_`.
- Remove all `.tmp_*` files after your are finished with an implementation