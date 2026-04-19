"""
Gemma 4 tool call parser.

Format: <|tool_call>call:func_name(arg1: "value1", arg2: "value2")<tool_call|>

Gemma 4 outputs tool calls in a Python function-call-like syntax wrapped
in <|tool_call> ... <tool_call|> tags.  Arguments use Python literal syntax
(strings with single or double quotes, ints, floats, dicts, lists).

Key characteristics observed from Gemma 4 (31B, 26B) via Nous/OpenRouter:
  - Tags: <|tool_call> (open) and <tool_call|> (close)
  - Body: call:function_name(kwarg1: value1, kwarg2: value2)
  - Values: Python literals — 'str', "str", 123, {dict}, [list]
  - Quotes: both single and double quotes used interchangeably
  - Multiple tool calls: each wrapped in its own tag pair
  - Korean and other Unicode: supported in string values

Reference: https://github.com/NousResearch/hermes-agent/issues/6626
"""

import ast
import json
import re
import uuid
from typing import List, Optional

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)

from environments.tool_call_parsers import ParseResult, ToolCallParser, register_parser

# Match <|tool_call>call:name(args)<tool_call|> with both closed and unclosed variants
_TOOL_CALL_RE = re.compile(
    r"<\|tool_call>\s*call:(\w+)\((.*?)\)\s*<tool_call\|>"
    r"|<\|tool_call>\s*call:(\w+)\((.*)",
    re.DOTALL,
)

# Match <|tool_call>call:name{args}<tool_call|> (alternate brace syntax from issue #6626)
_TOOL_CALL_BRACE_RE = re.compile(
    r"<\|tool_call>\s*call:(\w+)\{(.*?)\}\s*<tool_call\|>"
    r"|<\|tool_call>\s*call:(\w+)\{(.*)",
    re.DOTALL,
)


def _parse_kwargs_to_dict(raw: str) -> dict:
    """Parse Python-style keyword arguments into a dict.

    Handles formats like:
      query: "blockchain news"
      target: '#channel', message: 'hello'
      title: 'DB', properties: {'name': 'text', 'dept': 'select'}
      database: 'Members', name: 'Alice', priority: 1
    """
    raw = raw.strip()
    if not raw:
        return {}

    # Try parsing as a Python dict literal first (brace syntax)
    # e.g. {pattern: "/var/log", target: "files"}
    try:
        # Wrap bare keys with quotes for ast.literal_eval
        result = ast.literal_eval("{" + raw + "}")
        if isinstance(result, dict):
            return result
    except (ValueError, SyntaxError):
        pass

    # Parse key: value pairs manually
    result = {}
    # Split on commas that are not inside quotes or nested structures
    depth = 0
    current = ""
    pairs = []
    in_single_quote = False
    in_double_quote = False

    for char in raw:
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current += char
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current += char
        elif char in ("(", "[", "{") and not in_single_quote and not in_double_quote:
            depth += 1
            current += char
        elif char in (")", "]", "}") and not in_single_quote and not in_double_quote:
            depth -= 1
            current += char
        elif char == "," and depth == 0 and not in_single_quote and not in_double_quote:
            pairs.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        pairs.append(current.strip())

    for pair in pairs:
        # Find the first colon that is not inside quotes or nested structures
        colon_idx = -1
        in_sq = False
        in_dq = False
        nest = 0
        for i, ch in enumerate(pair):
            if ch == "'" and not in_dq:
                in_sq = not in_sq
            elif ch == '"' and not in_sq:
                in_dq = not in_dq
            elif ch in ("(", "[", "{") and not in_sq and not in_dq:
                nest += 1
            elif ch in (")", "]", "}") and not in_sq and not in_dq:
                nest -= 1
            elif ch in (":", "=") and not in_sq and not in_dq and nest == 0:
                colon_idx = i
                break

        if colon_idx == -1:
            continue

        key = pair[:colon_idx].strip().strip("'\"")
        value_str = pair[colon_idx + 1:].strip()

        # Parse the value
        try:
            value = ast.literal_eval(value_str)
        except (ValueError, SyntaxError):
            # Fall back to string
            value = value_str.strip("'\"")

        result[key] = value

    return result


def _parse_brace_kwargs(raw: str) -> dict:
    """Parse brace-syntax kwargs: pattern:<|"|>value<|"|>,target:<|"|>value<|"|>

    This handles the format reported in issue #6626 where Gemma uses
    <|"|> as quote delimiters instead of regular quotes.
    """
    raw = raw.strip()
    if not raw:
        return {}

    # Replace Gemma's special quote tokens with regular quotes
    cleaned = raw.replace('<|"|>', '"')

    # Try parsing as dict
    try:
        result = ast.literal_eval("{" + cleaned + "}")
        if isinstance(result, dict):
            return result
    except (ValueError, SyntaxError):
        pass

    # Fall back to manual parsing
    return _parse_kwargs_to_dict(cleaned)


@register_parser("gemma4")
class Gemma4ToolCallParser(ToolCallParser):
    """
    Parser for Gemma 4 tool calls.

    Matches <|tool_call>call:name(args)<tool_call|> tags and extracts
    function name and arguments.  Also handles the brace-syntax variant
    <|tool_call>call:name{args}<tool_call|> reported in issue #6626.
    """

    def parse(self, text: str) -> ParseResult:
        if "<|tool_call>" not in text:
            return text, None

        try:
            tool_calls: List[ChatCompletionMessageToolCall] = []

            # Try parenthesis syntax first: call:name(args)
            matches = _TOOL_CALL_RE.findall(text)
            for match in matches:
                # match is (closed_name, closed_args, unclosed_name, unclosed_args)
                name = match[0] if match[0] else match[2]
                raw_args = match[1] if match[0] else match[3]

                if not name:
                    continue

                arguments = _parse_kwargs_to_dict(raw_args)
                tool_calls.append(
                    ChatCompletionMessageToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        type="function",
                        function=Function(
                            name=name,
                            arguments=json.dumps(arguments, ensure_ascii=False),
                        ),
                    )
                )

            # Try brace syntax: call:name{args}
            if not tool_calls:
                matches = _TOOL_CALL_BRACE_RE.findall(text)
                for match in matches:
                    name = match[0] if match[0] else match[2]
                    raw_args = match[1] if match[0] else match[3]

                    if not name:
                        continue

                    arguments = _parse_brace_kwargs(raw_args)
                    tool_calls.append(
                        ChatCompletionMessageToolCall(
                            id=f"call_{uuid.uuid4().hex[:8]}",
                            type="function",
                            function=Function(
                                name=name,
                                arguments=json.dumps(arguments, ensure_ascii=False),
                            ),
                        )
                    )

            if not tool_calls:
                return text, None

            # Content is everything before the first <|tool_call> tag
            first_tag = text.find("<|tool_call>")
            content = text[:first_tag].strip() if first_tag > 0 else None
            return content, tool_calls

        except Exception:
            return text, None
