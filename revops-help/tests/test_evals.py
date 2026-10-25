"""Offline check of the eval runner with a fake Claude."""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evals"))

import run_evals  # noqa: E402


class FakeClaude:
    """Answers every question; the judge passes everything except T20."""
    def __init__(self):
        self.messages = self

    def create(self, **kwargs):
        prompt = kwargs["messages"][0]["content"]
        if isinstance(prompt, str) and prompt.startswith("You are marking"):
            verdict = "FAIL" if "discount policy" in prompt else "PASS"
            text = f'Sure: {{"verdict": "{verdict}", "reason": "test reason"}}'
        else:
            text = "An answer."
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=text)])


def test_runner_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(run_evals, "HERE", run_evals.HERE)  # real test_set.csv
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert run_evals.main(["--only", "T01,T20"], client=FakeClaude()) == 0
    text = summary.read_text()
    assert "1/2 passed" in text
    assert "<b>T20</b>" in text and "<b>T01</b>" not in text


def test_all_tests_load():
    tests = run_evals.load_tests()
    assert len(tests) == 21
    assert all(t["question"] and t["must_include"] for t in tests)
