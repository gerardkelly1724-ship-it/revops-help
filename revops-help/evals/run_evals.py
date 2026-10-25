"""
Test runner ("evals") for the RevOps assistant.

For each question in test_set.csv:
  1. Ask the assistant, exactly as the website would.
  2. Ask a second Claude call (the "judge") to mark the answer PASS or FAIL
     against what a good answer must include and must not do.
  3. Write a scorecard.

Run all questions:        python evals/run_evals.py
Run just some:            python evals/run_evals.py --only T05,T17
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import anthropic

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # so we can import assistant.py

import assistant  # noqa: E402

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", assistant.MODEL)
PARALLEL = 3  # questions run at the same time; keep low on a new API account

JUDGE_PROMPT = """You are marking an AI assistant's answer to a RevOps question.

Question: {question}

What it should do: {expected_behaviour}
A good answer must include: {must_include}
A good answer must NOT: {must_not_do}

HubSpot lookups the assistant made: {tools_used}

The assistant's answer:
<answer>
{answer}
</answer>

Mark it PASS if it does what it should, includes the key points (wording can differ), and does none of the "must not" things. Mark it FAIL otherwise. Don't fail it for extra detail, minor style issues, or for noting that the test portal differs from the docs. Do fail it for wrong facts, invented company policy, or claiming to have changed data.

Reply with JSON only, like this:
{{"verdict": "PASS", "reason": "one short sentence, under 25 words"}}"""


def load_tests(only=None):
    with open(HERE / "test_set.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if only:
        wanted = {x.strip().upper() for x in only.split(",")}
        rows = [r for r in rows if r["id"].upper() in wanted]
    return rows


def judge(client, test, answer, tools_used):
    prompt = JUDGE_PROMPT.format(
        question=test["question"],
        expected_behaviour=test["expected_behaviour"],
        must_include=test["must_include"] or "(nothing specific)",
        must_not_do=test["must_not_do"] or "(nothing specific)",
        tools_used=", ".join(t["tool"] for t in tools_used) or "none",
        answer=answer,
    )
    resp = client.messages.create(
        model=JUDGE_MODEL, max_tokens=1000, messages=[{"role": "user", "content": prompt}]
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    match = re.search(r"\{.*\}", text, re.S)  # pull the JSON out even if there's extra text
    try:
        data = json.loads(match.group(0))
        verdict = "PASS" if str(data.get("verdict", "")).upper() == "PASS" else "FAIL"
        return verdict, data.get("reason", "")
    except Exception:  # noqa: BLE001
        return "FAIL", f"Judge reply couldn't be read: {text[:200]}"


def run_one(client, test):
    started = time.time()
    try:
        answer, tools_used = assistant.answer(
            [{"role": "user", "content": test["question"]}], client=client
        )
        verdict, reason = judge(client, test, answer, tools_used)
    except Exception as e:  # noqa: BLE001
        answer, tools_used = "", []
        verdict, reason = "ERROR", f"{type(e).__name__}: {e}"
    return {
        **test,
        "answer": answer,
        "tools_used": tools_used,
        "verdict": verdict,
        "reason": reason,
        "seconds": round(time.time() - started),
    }


def scorecard(results):
    passed = sum(r["verdict"] == "PASS" for r in results)
    icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️"}
    lines = [
        f"# RevOps Help evals: {passed}/{len(results)} passed",
        "",
        f"Run {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC, model `{assistant.MODEL}`",
        "",
        "| | Test | Question | Lookups | Why |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        q = r["question"].replace("|", "/")
        why = r["reason"].replace("|", "/").replace("\n", " ")
        lines.append(f"| {icon[r['verdict']]} | {r['id']} | {q} | {len(r['tools_used'])} | {why} |")

    not_passed = [r for r in results if r["verdict"] != "PASS"]
    if not_passed:
        lines += ["", "## Answers that didn't pass", ""]
        for r in not_passed:
            lines += [
                f"<details><summary><b>{r['id']}</b>: {r['question']}</summary>",
                "",
                f"**Should include:** {r['must_include']}",
                "",
                f"**Lookups:** {', '.join(t['tool'] for t in r['tools_used']) or 'none'}",
                "",
                r["answer"] or "_(no answer)_",
                "",
                "</details>",
                "",
            ]
    return "\n".join(lines), passed


def main(argv=None, client=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="comma-separated test IDs, e.g. T05,T17")
    args = parser.parse_args(argv)

    tests = load_tests(args.only)
    if not tests:
        print("No matching tests.")
        return 1
    client = client or anthropic.Anthropic()

    print(f"Running {len(tests)} tests...")
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        results = list(pool.map(lambda t: run_one(client, t), tests))
    for r in results:
        print(f"{r['verdict']:5} {r['id']}  {r['reason']}")

    report, passed = scorecard(results)
    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    (out_dir / f"results-{stamp}.md").write_text(report, encoding="utf-8")
    (out_dir / f"results-{stamp}.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

    # On GitHub, this shows the scorecard on the run's summary page
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(report)

    print(f"\n{passed}/{len(results)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
