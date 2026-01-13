---
auto_execution_mode: 1
---
Check if the user has given you a [SESSION_FOLDER] to work in.
If not, create one in the root folder with the naming scheme
`/_YYYY-MM-DD_[PROBLEM_DESCRIPTION]/`

[PROBLEM_DESCRIPTION] should contain only alphanumerical characters without spaces.

In the [SESSION_FOLDER] folder, create a `PROBLEMS.md`, `PROGRESS.md` and `NOTES.md` file.
In this folder you will place all [SESSION_DOCUMENTS].

**[SESSION_DOCUMENTS]**:
- Information Document: `_INFO_[SPEC_TOPIC].md`
- Specifications: `_SPEC_[SPEC_TOPIC].md`
- Implementation plans: `_IMPL_[SPEC_TOPIC].md`
- Problem tracker: `PROBLEMS.md` - to keep track of all problems that the user brings in and that pop up in the session
- Progress tracker: `PROGRESS.md` - to keep track of 1) all things to do, 2) already done, 3) already tried but not used
- Knowledge tracker: `NOTES.md` - to keep track of all information and code that need to be remembered across sessions and agents. 

Read the rules in the windsurf rules folder again and write the most important rules into the `NOTES.md` file into a section at the top `# IMPORTANT: Cascade Agent Instructions`
Example: Don't use tables in markdown files.