---
name: feishu-workbench
description: >
  Use Hermes with Feishu/Lark as a practical workbench: diagnose Feishu auth,
  read and search messages, work with docs/wiki/drive, and handle sheets,
  bitable, calendar, and task workflows with discovery-first safety.
  Use when the user asks Hermes to operate inside Feishu/Lark, troubleshoot
  Feishu permissions, summarize Feishu conversations, or update Feishu office
  resources.
version: 1.0.0
author: guhaigg, enhanced by Hermes Agent
license: MIT
category: communication
metadata:
  hermes:
    tags: [Feishu, Lark, Communication, Office, OAuth, Messaging, Docs, Sheets, Calendar, Tasks]
---

# Feishu Workbench

Use this skill when the user wants Hermes to work inside Feishu/Lark or to
troubleshoot Feishu/Lark connectivity. The skill does not add new Feishu API
tools by itself; it tells Hermes how to use the Feishu gateway and Feishu tools
that are already available in the current installation.

## When to Use

Use this skill when the user asks to:

- connect, diagnose, or repair Feishu/Lark authorization
- explain why Feishu search, docs, sheets, calendar, or task access is failing
- read or summarize Feishu conversations, topics, threads, or message history
- search Feishu messages, docs, wiki pages, or drive files
- update Feishu docs, wiki pages, sheets, bitable records, calendar events, or tasks
- enumerate resources such as available chats, documents, bases, sheets,
  calendars, tasklists, or tasks before acting on them

Do not use this skill for unrelated office tools, non-Feishu chat platforms, or
generic OAuth questions with no Feishu/Lark context.

## Core Response Contract

For Feishu work, keep the answer operational and compact:

1. **State the outcome first.**
2. **State the exact limitation if blocked.**
3. **State the next action that unblocks the task.**

Avoid:

- raw OAuth URLs unless the user explicitly asks for them
- long scope dumps when a capability summary is enough
- internal traces, tool-debug prose, or implementation commentary
- saying "nothing exists" when the observed result only proves "nothing was
  visible in this query"

## Auth and Doctor Workflow

When Feishu behavior looks broken, check auth before guessing.

Preferred order:

1. Use `/feishu diagnose` or the closest available diagnostic command for a
   compact status check.
2. Use `/feishu doctor` when the user needs the full capability matrix.
3. Use `/feishu auth` only when user OAuth is missing, expired, or missing
   newly required scopes.
4. After authorization, re-run the smallest failing operation rather than
   claiming the full system is fixed.

When reporting auth state, separate these cases:

- bot/app connection is running
- tenant/app token works
- user OAuth exists
- user OAuth has the required scopes
- the target resource is visible to the current user/app

Do not merge these into a vague "Feishu is connected" statement.

## Discovery-First Office Workflow

For docs, wiki, drive, sheets, bitable, calendar, and tasks:

1. **Discover** relevant resources.
   - Search or list candidate docs, wiki nodes, drive files, spreadsheets,
     bases, calendars, tasklists, or tasks.
2. **Read** the specific target.
   - Confirm title, identifier, current content, sheet/table names, or event
     details before writing.
3. **Act** only after the target is clear.
   - Update the smallest possible object.
   - Ask for confirmation before destructive or broad changes.
4. **Verify** by reading back the changed object or reporting the returned ID.

If discovery returns zero results, say what was searched and what boundary was
tested. For example:

- "No matching docs were visible to the current user OAuth query."
- "The app token works, but this operation needs user OAuth."
- "The query returned no records in this base/table; that does not prove the
  whole Feishu account has no records."

## Messaging Workflow

For Feishu chat and message work:

1. Prefer explicit identifiers when available:
   - `chat_id`
   - `thread_id`
   - `message_id`
   - user `open_id` / `union_id`
2. Read the narrowest relevant context first.
   - If there is a thread, read the thread.
   - If there is a message ID, read around that message.
   - If there is only a chat, read recent chat history.
   - Search messages only when there is no narrower target.
3. Distinguish bot-readable messages from user-readable history.
   - Message search and personal history usually require user OAuth.
   - Sending as a bot and sending as a user are different capabilities.
4. For user-visible sends, preview the recipient and message before sending if
   the content is not trivial.

For reaction or lightweight acknowledgement tasks, confirm the target message
and emoji/reaction name, then perform the smallest operation.

## Write Safety

Ask for confirmation before:

- deleting documents, records, sheets, tasks, events, or messages
- overwriting a document or spreadsheet range
- batch editing multiple records
- sending messages to many users or groups
- creating or changing calendar invitations that notify attendees

For safe read-only tasks, proceed without asking unnecessary questions.

## Tool Selection Guidance

When multiple Feishu tools are available:

- Prefer list/search/discovery tools before mutation tools.
- Prefer exact-object fetch tools over broad search once an ID is known.
- Prefer user OAuth tools for user-visible resources and personal search.
- Prefer app/bot tools for bot-owned messaging or app-level diagnostics.
- If a tool fails with permission or scope errors, report the missing capability
  directly and do not retry unrelated tools randomly.

## Verification

Before calling a Feishu task done, verify at least one of:

- the diagnostic command reports the expected auth state
- the target resource was read successfully
- the mutation response returned a stable ID or success marker
- a follow-up read confirms the change

If verification cannot be performed, say so explicitly and provide the next
minimal command or authorization step.
