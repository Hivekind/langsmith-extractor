---
description: Rules for git commit behavior
globs:
alwaysApply: true
version: 1.0
encoding: UTF-8
---

# Git Commit Rules

## IMPORTANT: No Automatic Commits

**NEVER create git commits without explicit user approval.**

### Rules:
1. **DO NOT** run `git commit` unless the user explicitly asks you to "create a commit" or "commit the changes"
2. **DO** make code changes and stage them with `git add` when requested
3. **DO** show the user what changes have been made with `git status` and `git diff`
4. **DO** wait for explicit approval before creating commits

### Acceptable user requests for commits:
- "create a commit"
- "commit these changes"
- "make a commit"
- "commit the code"

### NOT acceptable (do not commit):
- "save the changes" (just means write to files)
- "implement this feature" (just means write code)
- "fix this bug" (just means modify code)
- User asking you to "finish" or "complete" a task

### When changes are ready:
Instead of creating a commit, inform the user:
"The changes are ready for your review. You can see them with `git status` and `git diff`. Let me know if you'd like me to create a commit."

This ensures the user maintains full control over their git history and can review all changes before they are committed.