# PMO as Code — Specification

**Version 0.1.0 (Draft)** · July 2026 · © 2026 C4G Enterprises Inc. · Apache-2.0

PMO as Code is a vendor-neutral standard for running a project management
office from version-controlled, declarative files: business documents are
structured Markdown, validated like code on every change; requirements trace
end to end through typed links; and project status is derived from the
documents rather than self-reported.

This document specifies the standard precisely enough that an independent
implementation can be built against it. The reference implementation is
[docassert](https://github.com/c4g-john/docassert) (non-normative; see
Appendix C).

## 1. Conformance

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY**
are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

This specification defines two conformance targets:

- A **conforming repository**: a version-controlled tree of documents that
  satisfies the layout, identity, and grammar requirements of §3–§7.
- A **conforming processor**: software that evaluates a repository against
  §8–§11 (checks, profiles, derived status) with the blocking semantics given
  there.

Requirements on "a repository" bind authors and generators of content;
requirements on "a processor" bind implementations.

## 2. Terminology

- **Document** — one Markdown file with YAML frontmatter; the unit of review.
- **Kind** — a document type (e.g. `charter`, `brd`), defined by a template,
  a frontmatter schema, and audit criteria (§7).
- **Project** — the unit of delivery. Every document belongs to exactly one
  project, anchored by a **project anchor** (a document of kind `project`).
- **Item** — a traceable row inside a document (a requirement, criterion,
  test, risk, or decision) with a stable id and typed links (§6).
- **Relation** — the typed meaning of a link between items (§6.3).
- **Check** — a named evaluation of a document or a repository. Checks are
  **structural** (deterministic) or **semantic** (judgment-based) (§8).
- **Profile** — a named declaration of the document kinds a project is
  expected to carry (§9).
- **Approved**, as a predicate on a document: its `status` is `approved` or
  `baselined` (case-insensitive).

## 3. Repository layout

A conforming repository MUST keep its documents under a single documents tree
(canonically `documents/`; a processor MUST allow the location to be
overridden) organized **project-first**:

```
documents/
  <PROJECT-ID>/           e.g. documents/PRJ-001-AUR/
    project.md            the project anchor (exactly one per project folder)
    <kind>.md             e.g. charter.md, brd.md, prd.md
    status-reports/       dated status reports (RECOMMENDED layout)
      <YYYY-MM-DD>.md
```

- Each project folder SHOULD be named by the project's id.
- A repository MAY carry a generated project registry (`projects.yaml`) and a
  generated status snapshot (`STATUS.md`); see §11.
- Configuration (kind schemas, criteria, profiles, consistency rules) MAY be
  present in the repository. A processor MUST resolve configuration as
  **local override → processor defaults**: a file present in the repository
  wins over the processor's built-in equivalent.

## 4. Document model

A document MUST consist of a YAML frontmatter block delimited by `---` lines,
followed by a Markdown body.

### 4.1 Common frontmatter

Every document MUST carry:

| Field | Requirement |
|---|---|
| `kind` | one of the repository's kinds (§7) |
| `id` | the document id (§5.2); unique across the repository |
| `status` | the document lifecycle state (§4.3) |

Every document other than a project anchor MUST also carry:

| Field | Requirement |
|---|---|
| `project` | the owning project's id (§5.1) |
| `title` | a human-readable title, ≥ 3 characters |

Kinds add further fields via their schema (e.g. `sponsor`, `budget`, `dates`
for `charter`; `owner` for most others; `period` and `rag` for
`status-report`). Unknown extra fields SHOULD be permitted.

### 4.2 Sections

The body is divided into **sections** by level-2 headings (`## Title`).
Section titles are the structural unit that criteria reference (required
sections, item sections, step sections). A section is **empty** if it contains
no content other than whitespace and HTML comments.

### 4.3 Document lifecycle

`status` MUST be one of `draft`, `proposed`, `approved`, `baselined` (a kind
MAY restrict this set; `charter` in the standard library omits `baselined`).
The **approved** predicate (§2) gates the stricter cross-document checks
(§8.3): work-in-progress MUST NOT be blocked for incompleteness.

A project anchor uses a different lifecycle: `proposed`, `active`, `on-hold`,
`closed` (§5.1).

## 5. Identity

Identity is hierarchical and self-describing: the project code namespaces
every document id and item id beneath it.

### 5.1 Projects

Each project MUST be declared by exactly one **project anchor**: a document of
kind `project` with frontmatter:

| Field | Requirement |
|---|---|
| `id` | MUST match `^PRJ-\d{3,}-[A-Z]{2,6}$` (e.g. `PRJ-001-AUR`) |
| `code` | MUST match `^[A-Z]{2,6}$` and MUST equal the trailing segment of `id` |
| `name` | human-readable name, ≥ 3 characters |
| `sponsor` | the accountable individual |
| `status` | one of `proposed`, `active`, `on-hold`, `closed` |
| `profile` | OPTIONAL; names a profile (§9) |

Across a repository, project `id`s MUST be unique and project `code`s MUST be
unique. The numeric segment SHOULD be assigned sequentially; the id, once
assigned, MUST NOT be reused for a different project.

### 5.2 Document ids

Document ids (other than project anchors, whose id is the project id) MUST
match `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$`, where the leading segment is the
owning project's `code` (e.g. `AUR-brd`, `AUR-status-2026-07-01`). Document
ids MUST be unique across the repository.

### 5.3 Item ids

Item ids MUST match:

```
^<CODE>-<TYPE>-<N>$   where  CODE = [A-Z]{2,6}   (the owning project's code)
                             TYPE = [A-Z]{2,6}   (the item type, §6.2)
                             N    = [0-9]+       (zero-padding to 3 digits RECOMMENDED)
```

e.g. `AUR-BR-001`, `AUR-NFR-05`. Item ids MUST be unique across the
repository. An item's CODE MUST equal the `code` of the project its document
belongs to. (The grammar is disjoint from project ids: `AUR-BR-001` is
letters-letters-digits; `PRJ-001-AUR` is letters-digits-letters.)

## 6. Traceable items

### 6.1 Item grammar

Within sections that a kind's criteria declare as **item sections**, every
top-level bullet MUST be an item of the form:

```
- **<ITEM-ID>** (<links>): <text>
- **<ITEM-ID>**: <text>
```

normatively, a bullet whose text matches:

```
^\*\*(?<id>(?<project>[A-Z]{2,6})-(?<type>[A-Z]{2,6})-\d+)\*\*(?:\s*\((?<links>[^)]*)\))?\s*:\s*(?<text>.+)$
```

The optional `links` clause is a `;`-separated list of groups, each
`relation: target[, target]…`:

```
(traces: AUR-BR-001, AUR-BR-003; verifies: AUR-FR-101)
```

Relation names MUST be treated case-insensitively (canonical form lowercase).
Targets are item ids; cross-project links are permitted and simply use the
other project's code.

### 6.2 Item types

The item's TYPE segment MUST equal the type its section declares. The standard
library (§7.2) defines the types `BR`, `PR`, `FR`, `NFR`, `AC`, `US`, `TC`,
`RISK`, `ADR`. Repositories MAY define further types via their criteria.

### 6.3 Standard relations

| Relation | From → To | Meaning |
|---|---|---|
| `traces` | child requirement → parent requirement | the child refines/implements the parent (PR→BR, FR/NFR→PR, US→PR) |
| `verifies` | acceptance criterion → requirement | the criterion verifies the requirement (AC→PR/FR) |
| `tests` | test case → acceptance criterion | the test exercises the criterion (TC→AC) |
| `threatens` | risk → requirement | the risk endangers the item (RISK→BR/PR) |
| `affects` | decision → requirement | the decision changes the item (ADR→FR/NFR) |

Repositories MAY define further relations; processors MUST apply referential
integrity (§8.3) to every relation, known or not.

## 7. Kinds

### 7.1 The kind mechanism

A kind is defined by three artifacts:

- a **template** — the canonical authoring shape;
- a **schema** — constraints on the kind's frontmatter (JSON Schema
  RECOMMENDED);
- **criteria** — the ordered list of checks for the kind, each declared with
  an id, a tier (`structural` | `semantic`), and whether it is `blocking`,
  plus the kind's `required_sections`, `item_sections`
  (`{section, prefix: TYPE}`), and any kind-specific check configuration.

Adding a kind MUST NOT require modifying this specification. Processors SHOULD
make common checks configuration-driven so new kinds need no code.

### 7.2 The standard kind library (v0.1)

| Kind | Purpose | Item types |
|---|---|---|
| `project` | the project anchor (§5.1) | — |
| `charter` | objective, measurable success criteria, sponsor, budget | — |
| `business-case` | problem, options, recommendation, costs, benefits | — |
| `brd` | business requirements | `BR` |
| `prd` | product requirements + acceptance criteria | `PR`, `AC` |
| `frnfr` | functional & non-functional requirements | `FR`, `NFR` |
| `user-story` | user stories in "As a… I want…" form | `US` |
| `test-cases` | test cases | `TC` |
| `adr` | architecture decisions with a recorded status | `ADR` |
| `risk-register` | risks with probability/impact/owner/response | `RISK` |
| `raci-stakeholder` | roles matrix; exactly one Accountable per activity | — |
| `qa-test-plan` | test strategy with measurable exit criteria | — |
| `data-migration-plan` | sources, field mapping, validation, cutover | — |
| `release-cutover-plan` | ordered cutover steps, rollback trigger | — |
| `rollback-plan` | trigger conditions, ordered rollback steps | — |
| `hypercare-plan` | support window, severities, measurable exit | — |
| `runbook` | operational procedures, monitoring, escalation | — |
| `status-report` | period, RAG, cites risks from the register | — |
| `post-implementation-review` | outcomes vs objectives, lessons | — |
| `benefits-realization` | measurable benefits vs the business case | — |

The reference artifacts (templates, schemas, criteria) for this library ship
with the reference implementation and are normative for the library's kinds.

## 8. Checks

### 8.1 The two tiers

- **Structural checks** MUST be deterministic. A failing structural check
  marked blocking MUST be able to fail the evaluation (non-zero exit /
  failing CI status), which is what makes the gate real.
- **Semantic checks** (AI- or human-judgment-based) MUST NOT block. They are
  advisory: a processor MUST NOT let a semantic failure affect its blocking
  outcome, and MUST degrade gracefully (skip, not fail) when the judgment
  backend is unavailable.

### 8.2 Per-document evaluation

For each document, a processor MUST evaluate the checks its kind's criteria
declare, including at minimum: frontmatter validity against the kind's
schema; presence and non-emptiness of the kind's required sections; the item
grammar of §6.1 in every declared item section (including that each item's
TYPE matches the section and its CODE matches the owning project); and
document-id uniqueness.

### 8.3 Cross-document evaluation

Over the repository's item graph, a processor MUST evaluate:

| Check | Blocks |
|---|---|
| **Item-id uniqueness** — no item id defined twice | always |
| **Referential integrity** — every link target exists | always |
| **Required links** — each item of a configured type declares its configured relation (e.g. every `PR` has `traces`) | only when the **item's document** is approved |
| **Coverage** — each item of a configured parent type has ≥ 1 child of the configured type linking via the configured relation (e.g. every `BR` is traced by a `PR`; computed per project via the code namespace) | only when the **parent's document** is approved |
| **Profile completeness** — §9 | only when the project is at its profile's `enforce_when` stage (an unknown profile name always blocks) |
| **Registry freshness** — a committed registry (§11.1) matches the anchors | always, when the registry is present |

The required-links and coverage rules MUST be configurable (which types,
which relations) without code changes.

## 9. Profiles

A profile declares the document kinds a project is expected to carry:

```yaml
name: <profile-name>
enforce_when: active          # the lifecycle stage at which gaps block
expects:
  required:    [<kind>, …]
  recommended: [<kind>, …]
```

A project opts in via `profile:` on its anchor; a project with no profile has
no completeness expectations. For each expected kind, its **state** is:

- **complete** — ≥ 1 document of that kind in the project is approved *and*
  passes its blocking structural checks;
- **incomplete** — present, but none complete;
- **missing** — no document of that kind.

A missing **required** kind MUST block (per §8.3) only once the project's
lifecycle status equals the profile's `enforce_when`; before that it is
advisory. **Recommended** kinds MUST NOT block at any stage. Processors SHOULD
surface the full per-kind state on the project's status output.

## 10. Derived status

Project and portfolio status MUST be **derived** from the documents; a
processor MUST NOT present a self-reported value as the derived status (a
status report's own `rag` MAY be used as one input signal).

The RECOMMENDED derivation, per project and for the portfolio rollup:

- **red** — anything objectively broken: an approved document failing its
  blocking checks, a broken reference, or an enforced profile gap (§9);
- **amber** — carrying risk or incompleteness: coverage gaps, open risks in
  the register, profile gaps not yet enforced, or a latest status report
  self-reporting amber/red;
- **green** — none of the above.

Processors SHOULD provide per-project status (documents, coverage, risks,
completeness) and a portfolio index, and SHOULD be able to render them for
publication.

## 11. Generated artifacts

Generated artifacts are derived views and MUST be reproducible from the
documents alone.

### 11.1 Project registry

A repository MAY commit a registry (canonically `projects.yaml`) listing every
project anchor (`id`, `code`, `name`, `sponsor`, `status`). If committed, a
processor MUST be able to verify it matches the anchors (§8.3 registry
freshness) so it cannot drift.

### 11.2 Traceability matrix

Processors SHOULD generate a requirements traceability matrix by walking
`BR → PR → FR/NFR → AC → TC` through the link graph, filterable per project.
The matrix is derived output and MUST NOT be hand-maintained as a source of
truth.

## 12. Conformance claims and versioning

This specification is versioned semantically; this document is
**v0.1.0 (Draft)**. Breaking changes to grammars or blocking semantics require
a major version. An implementation SHOULD claim conformance as: *"implements
PMO as Code v0.1"*. A claim MUST cover, at minimum: the document model (§4),
the identity grammars (§5), the item grammar and standard relations (§6), and
the check tiers and blocking rules (§8).

Changes to this specification are proposed as pull requests against its
repository.

---

## Appendix A — Grammar summary (normative)

```
project id     ^PRJ-\d{3,}-[A-Z]{2,6}$
project code   ^[A-Z]{2,6}$                       (must equal the id's tail)
document id    ^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$    (leading segment = project code)
item id        ^[A-Z]{2,6}-[A-Z]{2,6}-[0-9]+$     (CODE-TYPE-N)
item bullet    ^\*\*<item id>\*\*(\s*\(<links>\))?\s*:\s*<text>$
links clause   <relation>: <id>[, <id>]* [; <relation>: <id>[, <id>]*]*
doc lifecycle  draft | proposed | approved | baselined
project state  proposed | active | on-hold | closed
approved       status ∈ {approved, baselined}
```

## Appendix B — Reference implementation (non-normative)

[docassert](https://github.com/c4g-john/docassert) implements this
specification (`pip install docassert`), ships the standard kind library of
§7.2 as packaged defaults with local-override resolution (§3), and provides
the derived-status renderers of §10. A living conforming repository is
[pmo-as-code-pipeline](https://github.com/c4g-john/pmo-as-code-pipeline); a
starter is [pmo-as-code-template](https://github.com/c4g-john/pmo-as-code-template).
