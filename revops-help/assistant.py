"""
The brain of the app: builds the prompt and runs the conversation with Claude.

How one question flows through here:
  1. We send Claude the instructions, the knowledge docs, the conversation so
     far, and a list of HubSpot tools it may use.
  2. If Claude decides it needs data, it replies with a "tool_use" request
     instead of an answer, e.g. "run search_records for Keele".
  3. We run that tool, send the result back, and ask again.
  4. Steps 2 and 3 repeat until Claude replies with a normal answer.
"""

import os
from pathlib import Path

import anthropic

from hubspot_tools import TOOLS, run_tool

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_TOOL_ROUNDS = 10  # safety limit so a confused loop can't run forever

HERE = Path(__file__).parent


def build_system_prompt():
    """Instructions + routing procedure + every knowledge doc, as one prompt.

    The docs are small enough to send in full every time. This is the simple
    alternative to RAG (retrieval): instead of searching for the relevant doc,
    we give Claude all of them. It stops working once docs get too big, which
    is when you'd switch to retrieval.
    """
    instructions = (HERE / "prompts" / "instructions.md").read_text()
    procedure = (HERE / "prompts" / "diagnose-lead-routing.md").read_text()

    docs = []
    for path in sorted((HERE / "knowledge").glob("*.md")):
        docs.append(f'<doc name="{path.stem}">\n{path.read_text()}\n</doc>')

    return [
        {"type": "text", "text": instructions},
        {
            "type": "text",
            "text": "# Procedure: diagnose lead routing\n\n" + procedure
            + "\n\n# Knowledge docs\n\n" + "\n\n".join(docs),
            # Prompt caching: this block is identical on every request, so
            # Anthropic can reuse it instead of reprocessing it. Cheaper and faster.
            "cache_control": {"type": "ephemeral"},
        },
    ]


SYSTEM = build_system_prompt()


def answer(history, client=None):
    """history: list of {"role": "user"|"assistant", "content": "text"}.
    Returns (reply_text, list_of_tools_used)."""
    client = client or anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    tools_used = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            return text, tools_used

        # Claude asked for one or more tools. Run each and send the results back.
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                tools_used.append({"tool": block.name, "input": block.input})
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": run_tool(block.name, block.input),
                })
        messages.append({"role": "user", "content": results})

    return "Sorry, that took too many lookups. Try a more specific question.", tools_used
