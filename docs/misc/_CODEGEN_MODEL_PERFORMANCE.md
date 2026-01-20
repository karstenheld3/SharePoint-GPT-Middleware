# AI Model Performance Tests

## Specification understanding

Model spec understanding results (10 test questions).

- **Test spec:** [_V2_SPEC_ROUTERS.md](_V2_SPEC_ROUTERS.md)
- **Test questions / answers:** [_V2_SPEC_ROUTERS_02-ANSWERS.md](_V2_SPEC_ROUTERS_02-ANSWERS.md)
- **Judge model:** GPT-5.2 Medium Reasoning

Judge model prompt:
```
Now rate the given answers against the reference answers and assign an **integer score from 0 to 5** where:
- Score 0 = completely unrelated and incorrect - FAIL
- Score 1 = related but completely incorrect - FAIL
- Score 2 = mostly incorrect - FAIL
- Score 3 = partially correct - FAIL
- Score 4 = mostly correct - PASS
- Score 5 = completely correct - PASS
Create a question scoring table and calculate the overall PASS / TOTAL ratio in percent.
```

Bare models:
- GPT-5.2 (ChatGPT): 100%

Models in Windsurf [Cost as of 2025-12-13]:
- [Free] GPT-5.2 Medium Reasoning: 100%
- [2x] Claude Sonnet 3.7: 100%
- [3x] Claude Sonnet 3.7 (Thinking): 60%, 60% **<- BAD**
- [2x] Claude Sonnet 4.0: 100%, 100%
- [3x] Claude Sonnet 4.0 (Thinking): 100%, 100%
- [2x] Claude Sonnet 4.5: 70%, 100%, 60%  **<- BAD**
- [3x] Claude Sonnet 4.5 (Thinking): 100%
- [2x] Claude Opus 4.5: 100%, 100%
- [3x] Claude Opus 4.5 (Thinking): 100%

## Specification implementation

### 2025-12-15 GPT-5.2 Medium Reasoning Fast vs. Claude Opus 4.5 (Thinking)

#### Task

- **Reading and parsing specification documents** - Models read _V2_SPEC_ROUTERS.md lines 1141-1354 containing example endpoint implementation
- **Context priming** - Reading 6 md files + 5 Python files (~35k tokens) to understand existing codebase patterns
- **Replicating template source code with minimal changes** - Copying the v2a implementation pattern to create v2b (or vice versa)
- **String substitution** - Changing /v2/ to /v2a/ or /v2b/ prefixes, and routers_v2 to routers_v2a or routers_v2b
- **Creating new files in correct locations** - router_job_functions.py and demorouter.py in the new folder
- **Modifying existing file** - Adding import and router registration in app.py
- **Following existing code conventions** - Matching indentation, naming patterns, import style from the codebase
- **Understanding file relationships** - Import paths between modules (from routers_v2b.router_job_functions import ...)

**Complexity level**: Low-medium. Mostly mechanical code replication with path/prefix substitution. No algorithmic problem-solving or novel architecture decisions required.

**Workflow used to prime models:**
```
Make sure you have no duplicates in your read list.
Find all .md files in the workspace but ONLY in the /.windsurf/rules folder and all subfolders.
Read these files.

Then read:
- /src: app.py, utils.py, hardcoded_config.py, common_sharepoint_functions.py, common_openai_functions.py
- /: _V2_SPEC_JOBS_UI.md, _V2_SPEC_ROUTERS.md, SOPS.md

Return only a single line: "Read [x] md files, [z]k context tokens"
```

### GPT-5.2 Medium Reasoning Fast

**Prompt:**
```
@_V2_SPEC_ROUTERS.md#L1141-1354 Implement this with 2 important changes:

Instead of 
/src/routers_v2 
use
/src/routers_v2a

Instead of 
/v2/ prefix for routers
use
/v2a/ prefix for routers

```

**Results:**
- Implementation is working
- Forgot to implement `read_job_result()` in `router_job_functions.py`
  - Reason: No critical spec bug; minor “not explicit enough” area if you want to prevent future omissions.
- Forgot to /v2a/demorouter self-documentation
  - Reason: Minor ambiguity (router root doc format vs “bare GET always plaintext”), but the main miss is implementation, not the spec.
- Forgot to add new links to `app.py` as specified in [SOPS.md](SOPS.md)
  - Reason fixed: Added cross-reference -> **Depends on:** `SOPS.md` for implementation checklist.
- Time: 9m 45s  (1m 45s priming) 

### Claude Opus 4.5 (Thinking)

**Prompt:**
```
@_V2_SPEC_ROUTERS.md#L1141-1354 Implement this with 2 important changes:

Instead of 
/src/routers_v2 
use
/src/routers_v2b

Instead of 
/v2/ prefix for routers
use
/v2b/ prefix for routers
```
**Results:**
- Implementation is working
- Forgot to add new links to `app.py` as specified in [SOPS.md](SOPS.md)
  - Reason fixed: Added cross-reference -> **Depends on:** `SOPS.md` for implementation checklist.
- Time: 2m 59s (27s priming)