---
name: feedback-subagent-permissions
description: Subagents (backend-engineer, QA) were denied Write/Edit/Bash tools — do all file work in main conversation
metadata:
  type: feedback
---

Subagents (backend-engineer, QA-engineer) failed because Write, Edit, Bash, and PowerShell tools were denied in the sandbox environment.

**Why:** The user's permission settings restrict tool access for spawned agents.

**How to apply:** Do all file creation, editing, and shell commands directly in the main conversation. Do not delegate file-writing tasks to subagents. Subagents are only useful for read-only research in this environment.
