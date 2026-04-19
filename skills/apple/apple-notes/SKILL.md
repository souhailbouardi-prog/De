---
name: apple-notes
description: Manage Apple Notes natively on macOS via osascript and Notes automation (read, search, create, append, organize, move).
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Notes, Apple, macOS, note-taking]
    related_skills: [obsidian]
prerequisites:
  commands: [osascript]
---

# Apple Notes

Use Apple Notes natively through `osascript` and macOS Notes automation.

This version is optimized for agent-driven workflows on macOS:

- no third-party Apple Notes CLI
- no `brew tap` / `brew install` step
- no interactive wrapper required for common tasks
- better fit for repeated read, search, append, move, and organization workflows

## Prerequisites

- **macOS** with Notes.app
- `osascript` available (built into macOS)
- Grant Automation access to Notes.app when prompted (System Settings -> Privacy & Security -> Automation)

## When to Use

- User asks to read, search, create, or update Apple Notes
- Saving information to Notes.app for cross-device access
- Organizing notes into folders
- Moving notes between folders
- Reusing existing notes as project continuity context

## When NOT to Use

- Obsidian vault management -> use the `obsidian` skill
- Bear Notes -> separate app (not supported here)
- Quick agent-only notes -> use the `memory` tool instead
- Summarization or translation itself -> do that first, then use this skill to save the result

## Operating Rules

1. Prefer Apple Notes when the user wants native Apple sync across iPhone, iPad, and Mac
2. Search before creating when there is any chance the note already exists
3. Prefer append/update over replacing the whole note
4. Keep formatting structured and readable
5. Be conservative with move and delete
6. If the target note is ambiguous, stop and clarify instead of guessing

## Quick Reference

### List folders

```bash
osascript -e 'tell application "Notes" to get name of every folder'
```

### Search note titles in a folder

```bash
osascript -e 'tell application "Notes" to get name of every note of first folder whose name contains "Apple Notes"'
```

### Read a note body

```bash
osascript -e 'tell application "Notes" to get body of note "Apple Notes Skill Reference" of first folder'
```

### Create a note

```bash
osascript <<'EOF'
tell application "Notes"
    activate
    tell first folder
        make new note with properties {name:"Apple Notes Skill", body:"<h1>Apple Notes Skill</h1><br><div>Structured content goes here.</div>"}
    end tell
end tell
EOF
```

## Practical Workflows

### Read or Search Existing Notes

- Find the note first by title or nearby keywords
- If multiple notes match, narrow before reading
- Read only after identifying the target note confidently

### Create a New Note

- Search first if the title may already exist
- Choose the correct folder if known
- Use a clear title and readable structure

### Append or Update

- Prefer appending new sections rather than rewriting old content
- Preserve existing structure unless the user explicitly asks for cleanup
- Avoid destroying manually written content

### Create Folders

- Create folders only when a clear category does not already exist
- Use simple, stable names
- Prefer flat folder names over pseudo-nested folder names

### Move Notes

- Identify the note first
- Confirm the destination folder
- For bulk moves, preview the mapping before executing

### Organize Uncategorized Notes

- First pass: move only high-confidence matches
- Second pass: create a few practical flat folders for recurring themes
- Final pass: move leftovers into a deliberate catch-all folder rather than leaving them unorganized forever

Classification is allowed when it directly supports organization, but keep it practical. Do not turn this skill into a deep taxonomy exercise.

## Formatting Rules

Never write dense wall-of-text notes if the content is more than a few lines.

Use:

- a clear title
- blank lines between paragraphs
- bullets for lists
- headings for sections

### Project update pattern

```md
# Project Name

## Update - YYYY-MM-DD

### Status

Short status summary.

### Done

- Item

### In Progress

- Item

### Next

- Item

### Risks / Blockers

- Item
```

## Limitations

- Apple Notes access depends on macOS Automation permission
- Rich text body may be returned as HTML-like content
- Raw body may include tags such as `<div>` or `<br>`
- Apple Notes organization is flatter and simpler than a full document system
- Avoid direct overwrite when append is safer

## Error Handling

When an action fails:

- check whether Automation permission is blocked
- check whether the folder exists
- check whether the note title is ambiguous
- retry the same validated `osascript` method before inventing a new access path
