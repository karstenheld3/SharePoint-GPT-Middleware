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
- [3x] Claude Sonnet 3.7 (Thinking): 60%, 60%
- [2x] Claude Sonnet 4.0: 100%, 100%
- [3x] Claude Sonnet 4.0 (Thinking): 100%, 100%
- [2x] Claude Sonnet 4.5: 70%, 100%, 60%
- [3x] Claude Sonnet 4.5 (Thinking): 100%
- [2x] Claude Opus 4.5: 100%, 100%
- [3x] Claude Opus 4.5 (Thinking): 100%