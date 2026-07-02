# Conformance suite

Machine-checkable conformance for PMO as Code processors (SPEC.md v0.3).
64 cases covering the grammars, the standard-library checks (including the
draft/proposed severity split), the cross-document graph checks, profiles, and
the registry.

## Run it against a processor

```bash
python3 conformance/runner.py --adapter \
  "docassert {cmd} --documents-dir {docs} [report]--json {out}[/report]"
```

The adapter is a shell template for your processor: `{cmd}` is the case's
command line, `{docs}` the documents directory, `{out}` where the JSON verdict
report (SPEC.md §14.9, `schema/verdict.json`) must be written. The
`[report]…[/report]` segment is dropped for cases whose command produces no
report (registry checks assert exit status only).

Only `check_id`, `passed`, and `blocking` are compared. Wording (`detail`) and
advisory scores are not conformance.

A processor that passes all cases at a given spec tag may claim conformance to
that spec version. The suite is versioned with the specification; the
reference implementation runs it in CI on every change.

Fixtures use the fictional projects `PRJ-001-CNF` / `PRJ-002-OTH` and are
deliberately minimal: each case is the smallest tree that exercises its rule.
