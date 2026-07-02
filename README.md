# PMO as Code — the specification

**[Read the spec → SPEC.md](SPEC.md)** · current version **v0.1.0 (Draft)**

PMO as Code is a vendor-neutral standard for running a PMO from
version-controlled, declarative files. This repository holds the normative
specification: the document model, the identity and item grammars, the typed
link relations, the two-tier check semantics (structural blocks, semantic
advises), profiles, and derived status.

The spec exists so that the standard is implementable by anyone — not just by
its reference implementation.

## The ecosystem

| | |
|---|---|
| The standard's site | https://c4g-john.github.io/pmo-as-code/ |
| Reference implementation | [docassert](https://github.com/c4g-john/docassert) · `pip install docassert` · [docassert.com](https://docassert.com) |
| CI action | [docassert-action](https://github.com/c4g-john/docassert-action) |
| Starter template | [pmo-as-code-template](https://github.com/c4g-john/pmo-as-code-template) |
| Living example | [pmo-as-code-pipeline](https://github.com/c4g-john/pmo-as-code-pipeline) ([dashboard](https://c4g-john.github.io/pmo-as-code-pipeline/)) |

## Proposing changes

Open a pull request against `SPEC.md`. Breaking changes to grammars or
blocking semantics require a major version bump; the spec is versioned
independently of any implementation.

## License

Apache-2.0 — see [LICENSE](LICENSE). © 2026 C4G Enterprises Inc.
