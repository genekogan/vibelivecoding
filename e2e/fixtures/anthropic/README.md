# Anthropic fixtures

Each fixture is a newline-delimited JSON (`.jsonl`) file. Each line is one SSE event object that the mock will stream as:

```
event: <type>
data: <json>
```

The scenario frontmatter's `anthropicFixtures` field lists an ordered queue of non-title fixtures the mock serves. Title-generation requests (detected by a system prompt containing the phrase `thread title`) are served from a separate `title` fixture.

Fixture kinds:
- **text reply** — `message_start`, `content_block_start(text)`, one or more `content_block_delta(text_delta)`, `content_block_stop`, `message_delta(stop_reason=end_turn)`, `message_stop`.
- **tool call** — `message_start`, `content_block_start(tool_use)`, `content_block_delta(input_json_delta)`, `content_block_stop`, `message_delta(stop_reason=tool_use)`, `message_stop`.
- **text after tool result** — like text reply but appears on the second POST (after the app sends `tool_result`).

Scenarios reference these by filename without extension.
