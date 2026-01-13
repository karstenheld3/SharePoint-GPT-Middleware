### Ambiguous Grammar

**RULE:** When a modifier (clause or phrase) can attach to multiple nouns, split into separate sentences.

**BAD:**
```
1. Files starting with '!' signify high relevance that must be treated with extra attention.
2. I saw the man with the telescope.
```
**PROBLEM:**
```
1. Files ... signify [high relevance] that must be treated...
                      └─────────────────┘
                      "that" binds here

2. I saw [the man] [with the telescope].
          └──┬──┘   └───────┬────────┘
   Interpretation A: I used the telescope to see the man
   Interpretation B: The man was holding the telescope
```
**GOOD:**
```
1. Files starting with '!' indicate high relevance. This information must be treated with extra attention.
2. I saw the man. He was holding a telescope.
```
