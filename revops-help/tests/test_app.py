"""
Offline tests: fake Claude and fake HubSpot, so these run without any keys.
Run with:  python -m pytest -q
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("APP_PASSWORD", "letmein")
os.environ.setdefault("HUBSPOT_PORTAL_ID", "123")

import app as webapp  # noqa: E402
import assistant  # noqa: E402
import hubspot_tools  # noqa: E402


# --- Fake Claude ------------------------------------------------------------

class FakeClaude:
    """First call asks for a tool, second call answers."""
    def __init__(self):
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return SimpleNamespace(
                stop_reason="tool_use",
                content=[SimpleNamespace(type="tool_use", id="t1", name="search_records",
                                         input={"object_type": "companies", "query": "Keele"})],
            )
        return SimpleNamespace(stop_reason="end_turn",
                               content=[SimpleNamespace(type="text", text="Keele is owned by Gerard.")])


def fake_hubspot(method, url, **kwargs):
    resp = mock.Mock()
    resp.raise_for_status = lambda: None
    resp.json = lambda: {"total": 1, "results": [{"id": "1", "properties": {"name": "Keele University", "hubspot_owner_id": "9", "website": ""}}]}
    return resp


# --- Tests ------------------------------------------------------------------

def test_system_prompt_includes_everything():
    text = "".join(b["text"] for b in assistant.SYSTEM)
    assert "RevOps help assistant" in text
    assert "Diagnose lead routing" in text
    assert text.count("<doc name=") == 7


def test_tool_loop_runs_tool_then_answers():
    fake = FakeClaude()
    with mock.patch.object(hubspot_tools.requests, "request", side_effect=fake_hubspot):
        reply, used = assistant.answer([{"role": "user", "content": "Who owns Keele?"}], client=fake)
    assert reply == "Keele is owned by Gerard."
    assert used == [{"tool": "search_records", "input": {"object_type": "companies", "query": "Keele"}}]
    # the tool result went back to Claude on the second call, with a link and empties removed
    tool_result = fake.calls[1]["messages"][-1]["content"][0]["content"]
    assert "Keele University" in tool_result and "/record/0-2/1" in tool_result and "website" not in tool_result


def test_writes_are_blocked():
    with pytest.raises(hubspot_tools.ReadOnlyError):
        hubspot_tools._request("PATCH", "/crm/v3/objects/contacts/1", json={})
    with pytest.raises(hubspot_tools.ReadOnlyError):
        hubspot_tools._request("POST", "/crm/v3/objects/contacts", json={})
    with pytest.raises(hubspot_tools.ReadOnlyError):
        hubspot_tools._request("DELETE", "/crm/v3/objects/contacts/1")


def test_tool_errors_come_back_as_text():
    out = hubspot_tools.run_tool("get_record", {"object_type": "contacts", "record_id": "x", "nope": 1})
    assert "error" in out


@pytest.fixture
def client():
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


def test_login_required(client):
    assert client.get("/").status_code == 302
    assert client.post("/api/chat", json={}).status_code == 401


def test_wrong_password(client):
    r = client.post("/login", data={"password": "nope"})
    assert b"not the password" in r.data


def test_chat_end_to_end(client):
    client.post("/login", data={"password": "letmein"})
    assert b"RevOps Help" in client.get("/").data
    with mock.patch.object(assistant, "answer", return_value=("Hello", [])):
        r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.get_json() == {"reply": "Hello", "tools_used": []}
