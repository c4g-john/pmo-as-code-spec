#!/usr/bin/env python3
"""PMO as Code conformance runner (tool-agnostic, stdlib only).

Runs every case under conformance/cases/ against a processor and checks its
JSON verdict report (SPEC.md §14.9) against the case's expectations.

Usage:
    python3 conformance/runner.py --adapter \\
        "docassert {cmd} --documents-dir {docs} [report]--json {out}[/report]"

The adapter is a shell command template. Placeholders:
    {cmd}   the case's command line from its `cmd` file
            (e.g. "validate documents/PRJ-001-CNF/charter.md")
    {docs}  the case's documents directory (absolute)
    {out}   where the processor must write its JSON report (absolute)
The command runs with the case's `tree/` directory as the working directory.

A case directory contains:
    tree/            the input (documents/..., optionally profiles/, projects.yaml)
    cmd              one line: the processor command
    expected.json    {"expect": [{"path", "check_id", "passed", "blocking"}...],
                      "exit_nonzero": bool (optional),
                      "no_report": bool (optional; strips the [report]…[/report] adapter segment)}

Only check_id / passed / blocking are compared (SPEC.md: detail wording and
score are not normative). `path` may be "*" to match any document in the
report. Exit status is asserted when `exit_nonzero` is present.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run_case(case: Path, adapter: str) -> list[str]:
    errors: list[str] = []
    tree = case / "tree"
    cmd_line = (case / "cmd").read_text().strip()
    expected = json.loads((case / "expected.json").read_text())

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "report.json"
        docs = tree / "documents"
        template = adapter
        if expected.get("no_report"):
            # strip the processor's report flag segment: "[report]--json {out}[/report]"
            import re as _re
            template = _re.sub(r"\[report\].*?\[/report\]", "", template)
        else:
            template = template.replace("[report]", "").replace("[/report]", "")
        shell_cmd = template.format(cmd=cmd_line, docs=str(docs), out=str(out))
        proc = subprocess.run(shlex.split(shell_cmd), cwd=tree,
                              capture_output=True, text=True)

        if "exit_nonzero" in expected:
            want_nonzero = bool(expected["exit_nonzero"])
            got_nonzero = proc.returncode != 0
            if want_nonzero != got_nonzero:
                errors.append(f"exit: wanted {'non-zero' if want_nonzero else 'zero'}, "
                              f"got {proc.returncode}\n  stderr: {proc.stderr.strip()[:200]}")

        if expected.get("no_report"):
            return errors
        if not out.is_file():
            errors.append(f"no report written\n  stderr: {proc.stderr.strip()[:200]}")
            return errors

        report = json.loads(out.read_text())
        docs_map = report.get("documents", {})

        for exp in expected.get("expect", []):
            path, cid = exp["path"], exp["check_id"]
            pools = list(docs_map.values()) if path == "*" else [docs_map.get(path, [])]
            hits = [r for pool in pools for r in pool if r.get("check_id") == cid]
            if not hits:
                errors.append(f"{cid}: not found in report for path {path!r} "
                              f"(paths present: {sorted(docs_map)[:4]})")
                continue
            match = any(r.get("passed") == exp["passed"] and
                        r.get("blocking") == exp["blocking"] for r in hits)
            if not match:
                got = [(r.get("passed"), r.get("blocking")) for r in hits]
                errors.append(f"{cid}: wanted passed={exp['passed']} "
                              f"blocking={exp['blocking']}, got {got}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True,
                    help='e.g. "docassert {cmd} --documents-dir {docs} --json {out}"')
    ap.add_argument("--only", help="run only cases whose path contains this substring")
    args = ap.parse_args()

    cases = sorted(p.parent for p in (HERE / "cases").rglob("expected.json"))
    if args.only:
        cases = [c for c in cases if args.only in str(c)]
    if not cases:
        print("no cases found", file=sys.stderr)
        return 2

    failed = 0
    for case in cases:
        rel = case.relative_to(HERE / "cases")
        errs = run_case(case, args.adapter)
        if errs:
            failed += 1
            print(f"FAIL {rel}")
            for e in errs:
                print(f"     {e}")
        else:
            print(f"pass {rel}")
    print(f"\n{len(cases) - failed}/{len(cases)} conformance cases pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
