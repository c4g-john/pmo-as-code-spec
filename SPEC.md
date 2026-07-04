# PMO as Code — Specification

**Version 0.8.0 (Draft)** · July 2026 · © 2026 C4G Enterprises Inc. · Apache-2.0

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
The lifecycle carries the check gradient — work-in-progress MUST NOT be
blocked for incompleteness:

- **draft** — work in progress: completeness checks (§8.2) are advisory;
- **proposed** — the document claims completeness: per-document completeness
  checks block;
- **approved / baselined** — the **approved** predicate (§2): the stricter
  cross-document checks (§8.3) also block.

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
| `repo` | OPTIONAL; `OWNER/NAME` of the code repository the project's execution bridge targets (Appendix C) |

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
| `after` | requirement → requirement | sequencing: the item is scoped to follow its target (PR→PR, same project) |
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
| `operations` | service catalog with levels/measures, `review_by` freshness | `SVC` |
| `post-implementation-review` | outcomes vs objectives, lessons | — |
| `benefits-realization` | measurable benefits vs the business case | — |

The library's field constraints, sections, item types, and check semantics are
specified normatively in §13. The machine-readable artifacts (templates,
schemas, criteria) ship with the reference implementation and are mirrored
informatively under `artifacts/` in this repository.

## 8. Checks

### 8.1 The two tiers

- **Structural checks** MUST be deterministic. A failing structural check
  marked blocking MUST be able to fail the evaluation (non-zero exit /
  failing CI status), which is what makes the gate real. Structural checks
  carry a **severity** (§8.2a): integrity checks block at any status;
  completeness checks are advisory for drafts.
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

### 8.2a Check severities

Every per-document structural check MUST be classified as one of:

- **integrity** (criteria `blocking: always`, the default) — violations mean
  the document is *malformed*: unparseable frontmatter, type/format/pattern/
  enum violations, a malformed or mistyped item bullet, a duplicate id, an
  invalid or inverted date. Integrity failures MUST block at any status,
  including drafts, because malformed data corrupts the graph.
- **completeness** (criteria `blocking: once-proposed`) — violations mean the
  document is *unfinished*: a schema-required field not yet present, an empty
  required section, an unmeasurable criterion, a risk without an owner.
  Completeness failures MUST be advisory while the document's status is
  `draft`, and MUST block once it is `proposed` or beyond. Processors MUST
  still report advisory completeness failures.

The standard library classifies missing required frontmatter as completeness
via a dedicated check (`frontmatter-complete`), keeping `frontmatter-schema`
as pure wellformedness.

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

A processor MUST report **red** whenever any red condition below holds; the
amber/green split is RECOMMENDED. Per project and for the portfolio rollup:

- **red** — anything objectively broken: an approved document failing its
  blocking checks, a broken reference, or an enforced profile gap (§9);
- **amber** — carrying risk or incompleteness: coverage gaps, open risks at
  or above the repository's **risk appetite** (below), an operations document
  whose `review_by` has passed (§13.21), profile gaps not yet enforced, or a
  latest status report self-reporting amber/red;
- **green** — none of the above.

*Risk appetite:* scoring probability and impact as low=1, medium=2, high=3,
critical=3, an open risk moves status to amber only when probability ×
impact meets the repository's threshold — default **6**, configurable as
`risk_amber_score` in `consistency.yaml` (`0` means any open risk ambers).
Open risks below the threshold remain fully reported as exposure; they are
recorded facts, not status defects. Rationale: a derivation in which any
open risk ambers forever punishes risk documentation and rewards empty
registers — the opposite of this standard's purpose.

*Scope-and-sequence presentation:* when presenting work, processors SHOULD
chart features by dependency sequence (`after` layers) and scope size —
recommended measure: **scope points** = traced stories + verifying
acceptance criteria, a pure document count involving no estimation — rather
than by a time axis. Recommended size labels over published buckets:
XS=1, S=2, M=3–4, L=5–7, XL=8+.

*Charter target milestone:* processors SHOULD treat an approved charter's
`dates.target` as an implicit dated milestone ("Charter target") wherever
dated milestones are presented (§13.2), so every chartered project has a
timeline anchor.

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
**v0.8.0 (Draft)** (0.2.0 introduced check severities, §8.2a; 0.3.0 made the standard library normative in §13, added processing details in §14, and introduced the conformance suite under `conformance/`; 0.3.1 added the
informative execution-mapping appendix; 0.3.2 added the optional `repo`
field on project anchors for bridge repository routing; 0.4.0 made the risk
lifecycle normative: the `Status` disposition field on `RISK` items, the
`risk-disposition-valid` check, and the derived-status rule that only
`open` risks signal amber; 0.5.0 added the `operations` kind (§13.21):
service catalogs with `Level`/`Measure` fields, the required `review_by`
date, and review staleness as an amber input to derived status; 0.6.0 made
dated charter milestones machine-readable (`- <label>: YYYY-MM-DD`, the
advisory `milestones-dated` check, temporal-fact presentation rule); 0.7.0
introduced the risk appetite: open risks amber derived status only at or
above `risk_amber_score` (default 6), and charters' `dates.target` became
an implicit milestone; 0.8.0 added the `after` sequencing relation with the
`sequence-acyclic` check and the scope-points presentation recommendation). Breaking changes to grammars or blocking semantics require
a major version. An implementation SHOULD claim conformance as: *"implements
PMO as Code v0.1"*. A claim MUST cover, at minimum: the document model (§4),
the identity grammars (§5), the item grammar and standard relations (§6), and
the check tiers and blocking rules (§8).

This specification is maintained by John Tanner at C4G Enterprises Inc.
Changes are proposed as pull requests against this repository. Removals or
incompatible changes are announced at least one minor version before they
take effect. A conforming processor SHOULD pass the conformance suite under
`conformance/` at the spec version it claims; the suite is versioned with the
specification.

## 13. The Standard Library (normative)

This section specifies the library of §7.2 precisely enough to implement
without reference to any implementation. For each kind: the frontmatter
constraints (equivalent to the mirrored JSON Schema), the required sections,
the item sections with their types, and the checks with their blocking modes
(§8.2a: `always` blocks at any status, `once-proposed` is advisory for drafts).

### 13.0 Check definitions

Checks marked *(config-driven)* take their section lists from the kind's
criteria (shown per kind below).

- **`frontmatter-schema`** (always) — the frontmatter is valid against the
  kind's field constraints, ignoring missing-required-field violations. Type,
  pattern, enum, format, and length violations fail here.
- **`frontmatter-complete`** (once-proposed) — no required field is missing.
- **`required-sections`** (once-proposed, config-driven) — every listed
  section is present and non-empty per §4.2.
- **`unique-id`** (always) — the document id is unique across the tree.
  Occurrences are compared by resolved file path, so the same file reached by
  two path spellings is not a duplicate.
- **`project-id-format`** (always; `project` kind) — `id` matches
  `^PRJ-\d{3,}-[A-Z]{2,6}$` and `code` equals the id's trailing segment.
- **`items-well-formed`** (always, config-driven) — every top-level bullet in
  each item section parses under the §6.1 grammar, its TYPE equals the
  section's declared type, and its CODE equals the owning project's code.
- **`dates-consistent`** (always) — if both `dates.created` and `dates.target`
  parse as dates, `target` MUST NOT precede `created`. A present but
  unparseable value fails. Absent values pass (their presence is
  `frontmatter-complete`'s concern).

**§13.0.M — the measurability predicate.** Text is *measurable* iff it
contains at least one digit AND matches at least one of:

```
comparator   [<>]=?  or a word from:
             below under above over "at least" "at most" "no more than"
             "no less than" "fewer than" "more than" "greater than"
             "less than" within by reach reduce increase decrease drop
             rise cut from to            (case-insensitive, word-bounded)
unit/symbol  %  $  €  £  /<digit>  an ISO date \d{4}-\d{2}-\d{2}  or a word from:
             hour(s) hr(s) day(s) week(s) month(s) minute(s) min(s)
             second(s) sec(s) USD EUR GBP k m bn pt(s) point(s) x
                                          (case-insensitive, word-bounded)
```

- **`measurable-success-criteria`** (once-proposed; `charter`) — every bullet
  in `Success Criteria` satisfies §13.0.M.
- **`measurable-items`** / **`measurable-exit-criteria`** (once-proposed,
  config-driven) — every bullet in each configured measurable section
  satisfies §13.0.M.

**§13.0.F — the field-extraction rule.** A labelled field inside an item or
bullet is `Field: value` where the field name is matched case-insensitively
and the value runs until a semicolon, a period followed by whitespace, a
period at end of line, or end of line. A value shorter than 2 characters
counts as absent. (So `Owner: alex.kim. Mitigation: dual-run.` yields
`alex.kim`.) Items are single source lines (§14.3); fields on later lines are
not found.

- **`risks-have-owner-and-mitigation`** (once-proposed; `charter`) — every
  bullet in `Risks` yields values for `Owner` and `Mitigation` per §13.0.F.
- **`risk-items-complete`** (once-proposed; `risk-register`) — every `RISK`
  item yields `Probability`, `Impact`, `Owner`, and `Response`.
- **`risk-disposition-valid`** (always; `risk-register`) — where a `RISK`
  item yields a `Status` field, its value (case-insensitive) is one of
  `open | mitigated | accepted | closed`. A `RISK` item without a `Status`
  field has the disposition `open`.
- **`sequence-acyclic`** (always; cross-document) — the directed graph of
  `after` links contains no cycle. A cycle is objectively broken sequencing
  and blocks like a broken reference.
- **`milestones-dated`** (never blocking; `charter`) — at least one
  `Milestones` bullet ends with an ISO date, so timelines have something to
  draw. Advisory only: undated milestone prose is legal.
- **`svc-items-complete`** (once-proposed; `operations`) — every `SVC` item
  yields `Level` and `Measure`.
- **`ops-review-fresh`** (never blocking; `operations`) — `review_by` is
  today or later; a past date reports as a failed advisory and feeds the
  derived-status amber rule (§10).
- **`adr-items-have-status`** (once-proposed; `adr`) — every `ADR` item
  yields `Status`, whose value (case-insensitive) is one of
  `proposed | accepted | superseded | deprecated | rejected`.
- **`story-format`** (once-proposed; `user-story`) — every `US` item's text,
  lowercased, contains `"as a "` or `"as an "`, and contains `"i want"`.
- **`numbered-steps`** (once-proposed, config-driven) — each configured steps
  section contains at least one line matching `^\s*\d+\.\s`.
- **`mapping-table`** (once-proposed; `data-migration-plan`) — the
  `Field Mapping` section contains a Markdown table with at least one data
  row: lines starting with `|`, minus any line containing `---` (the
  separator), minus the first remaining line (the header), leaves ≥ 1 row.
- **`raci-one-accountable`** (once-proposed; `raci-stakeholder`) — in the
  `RACI Matrix` section, take the lines starting with `|`, drop lines
  containing `---` and then the header line; every remaining row, split on
  `|`, has exactly one cell after the first whose trimmed, uppercased value
  is exactly `A`. (A combined cell such as `A/R` is not counted.)
- **`references-risk`** (once-proposed; `status-report`) — the
  `Risks & Issues` section is present and its body matches
  `\b[A-Z]{2,6}-RISK-\d+\b` at least once.
- **Semantic checks** (`objective-is-specific`,
  `success-criteria-verifiable`, and the cross-document alignment checks) are
  advisory per §8.1. Their scoring is implementation-defined; a processor
  MUST NOT let them block and MUST skip them gracefully when its judgment
  backend is unavailable.

### 13.1 `adr`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `adr` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Decisions`.
**Item sections:** `Decisions` → type `ADR`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `items-well-formed` | always |
| `adr-items-have-status` | once-proposed |
| `unique-id` | always |

### 13.2 `benefits-realization`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `benefits-realization` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Benefits`, `Measurement`, `Realized Value`.
**Measurable sections** (each bullet must satisfy §13.0.M): `Benefits`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `measurable-items` | once-proposed |
| `unique-id` | always |

### 13.3 `brd`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `brd` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Purpose`, `Business Requirements`, `Out of Scope`.
**Item sections:** `Business Requirements` → type `BR`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `items-well-formed` | always |
| `unique-id` | always |

### 13.4 `business-case`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `business-case` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `sponsor` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Problem Statement`, `Options Considered`, `Recommendation`, `Costs`, `Benefits`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `unique-id` | always |

### 13.5 `charter`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `charter` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `sponsor` | string | yes | minLength 2 |
| `budget` | object | yes | — |
| `budget.amount` | number | yes | > 0 |
| `budget.currency` | string | yes | pattern `^[A-Z]{3}$` |
| `dates` | object | yes | — |
| `dates.created` | string | yes | format `date` |
| `dates.target` | string | yes | format `date` |
| `status` | any | yes | one of `draft` / `proposed` / `approved` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Objective`, `Success Criteria`, `Scope`, `Milestones`, `Risks`, `Approval`.

Bullets in `Milestones` SHOULD end with an ISO date, separated from the
label by a colon or a dash: `- <label>: YYYY-MM-DD` or `- <label> — YYYY-MM-DD`.
Dated milestones are machine-readable — processors use them for timeline
views and next-milestone signals, always as **temporal facts** (elapsed,
today, upcoming): a milestone's date passing MUST NOT be presented as its
completion. Undated bullets are permitted and simply invisible to timelines.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `measurable-success-criteria` | once-proposed |
| `risks-have-owner-and-mitigation` | once-proposed |
| `dates-consistent` | always |
| `unique-id` | always |
| `objective-is-specific` | advisory (semantic) |
| `success-criteria-verifiable` | advisory (semantic) |

### 13.6 `data-migration-plan`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `data-migration-plan` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Scope`, `Source Systems`, `Field Mapping`, `Validation`, `Cutover`, `Rollback`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `mapping-table` | once-proposed |
| `unique-id` | always |

### 13.7 `frnfr`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `frnfr` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Functional Requirements`, `Non-Functional Requirements`.
**Item sections:** `Functional Requirements` → type `FR`; `Non-Functional Requirements` → type `NFR`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `items-well-formed` | always |
| `unique-id` | always |

### 13.8 `hypercare-plan`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `hypercare-plan` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Support Window`, `Severity Levels`, `Escalation`, `Exit Criteria`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `measurable-exit-criteria` | once-proposed |
| `unique-id` | always |

### 13.9 `post-implementation-review`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `post-implementation-review` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Summary`, `Outcomes vs Objectives`, `What Went Well`, `What Could Improve`, `Lessons Learned`, `Follow-up Actions`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `unique-id` | always |

### 13.10 `prd`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `prd` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Product Requirements`, `Acceptance Criteria`.
**Item sections:** `Product Requirements` → type `PR`; `Acceptance Criteria` → type `AC`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `items-well-formed` | always |
| `unique-id` | always |

### 13.11 `project`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `project` |
| `id` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |
| `code` | string | yes | pattern `^[A-Z]{2,6}$` |
| `name` | string | yes | minLength 3 |
| `sponsor` | string | yes | minLength 2 |
| `status` | any | yes | one of `proposed` / `active` / `on-hold` / `closed` |
| `profile` | string | no | — |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Scope`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `project-id-format` | always |
| `required-sections` | once-proposed |
| `unique-id` | always |

### 13.12 `qa-test-plan`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `qa-test-plan` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Scope`, `Test Approach`, `Environments`, `Entry Criteria`, `Exit Criteria`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `measurable-exit-criteria` | once-proposed |
| `unique-id` | always |

### 13.13 `raci-stakeholder`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `raci-stakeholder` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Stakeholders`, `RACI Matrix`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `raci-one-accountable` | once-proposed |
| `unique-id` | always |

### 13.14 `release-cutover-plan`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `release-cutover-plan` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Pre-Cutover Checklist`, `Cutover Steps`, `Verification`, `Rollback Trigger`.
**Steps sections** (§13.0 `numbered-steps`): `Cutover Steps`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `numbered-steps` | once-proposed |
| `unique-id` | always |

### 13.15 `risk-register`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `risk-register` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Risks`.
**Item sections:** `Risks` → type `RISK`.

`RISK` item text yields fields per §14's field grammar: `Probability`,
`Impact`, `Owner`, `Response` (see `risk-items-complete`), and OPTIONALLY
`Status` — the risk's disposition, one of `open`, `mitigated`, `accepted`,
or `closed` (case-insensitive). Absent `Status` means `open`. Only risks
whose disposition is `open` carry into the derived-status risk signal (§10);
dispositioned risks remain in the register as record.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `items-well-formed` | always |
| `risk-items-complete` | once-proposed |
| `risk-disposition-valid` | always |
| `unique-id` | always |

### 13.16 `rollback-plan`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `rollback-plan` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Trigger Conditions`, `Rollback Steps`, `Verification`.
**Steps sections** (§13.0 `numbered-steps`): `Rollback Steps`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `numbered-steps` | once-proposed |
| `unique-id` | always |

### 13.17 `runbook`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `runbook` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Prerequisites`, `Procedures`, `Monitoring`, `Escalation`.
**Steps sections** (§13.0 `numbered-steps`): `Procedures`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `numbered-steps` | once-proposed |
| `unique-id` | always |

### 13.18 `status-report`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `status-report` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `period` | string | yes | format `date` |
| `rag` | any | yes | one of `green` / `amber` / `red` |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Summary`, `Progress`, `Risks & Issues`, `Next Steps`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `references-risk` | once-proposed |
| `unique-id` | always |

### 13.19 `test-cases`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `test-cases` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Test Cases`.
**Item sections:** `Test Cases` → type `TC`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `items-well-formed` | always |
| `unique-id` | always |

### 13.20 `user-story`

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `user-story` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `User Stories`.
**Item sections:** `User Stories` → type `US`.

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `items-well-formed` | always |
| `story-format` | once-proposed |
| `unique-id` | always |


### 13.21 `operations`

The governance home for ongoing work: a service catalog with commitments,
chartered per operating period, whose freshness is part of derived status.

| Field | Type | Required | Constraints |
|---|---|---|---|
| `kind` | any | yes | const `operations` |
| `id` | string | yes | pattern `^[A-Z]{2,6}-[a-z0-9][a-z0-9-]*$` |
| `title` | string | yes | minLength 3 |
| `owner` | string | yes | minLength 2 |
| `status` | any | yes | one of `draft` / `proposed` / `approved` / `baselined` |
| `project` | string | yes | pattern `^PRJ-\d{3,}-[A-Z]{2,6}$` |
| `review_by` | string | yes | format `date` — the next operations review |

Additional frontmatter fields are permitted.

**Required sections:** `Overview`, `Services`.
**Item sections:** `Services` → type `SVC`.

`SVC` item text yields fields per §14's field grammar: `Level` (the service
commitment, which SHOULD be measurable per §14's measurability rule) and
`Measure` (how attainment is read).

| Check | Blocking |
|---|---|
| `frontmatter-schema` | always |
| `frontmatter-complete` | once-proposed |
| `required-sections` | once-proposed |
| `items-well-formed` | always |
| `svc-items-complete` | once-proposed |
| `ops-review-fresh` | never (advisory) |
| `unique-id` | always |

`ops-review-fresh` reports whether `review_by` is today or later. A past
`review_by` never blocks a merge; it is an **amber input to derived status**
(§10): a project whose operations document has a stale review is carrying
unreviewed operational commitments.

## 14. Processing details (normative)

- **14.1 Encoding.** Documents are UTF-8. Processors MUST accept LF line
  endings and SHOULD accept CRLF. Frontmatter is delimited by `---` lines
  beginning at the first line of the file.
- **14.2 Case.** Kind and profile names are lowercase and matched exactly.
  `status` values and relation names are matched case-insensitively.
- **14.3 Items are single source lines.** An item is exactly one line matching
  the §6.1 grammar. Subsequent lines, indented or not, are not part of the
  item's text; labelled fields (§13.0.F) MUST appear on the item's line.
- **14.4 Coverage is graph-wide.** A coverage rule is satisfied by any child
  of the configured type linking via the configured relation, regardless of
  the child's project. Per-project coverage figures in status output are a
  reporting scope, not check semantics.
- **14.5 Canonical registry serialization.** The generated registry is a YAML
  mapping with a single `projects` key holding a list of mappings, one per
  anchor, discovered in sorted-path order, each with exactly the keys
  `id, code, name, sponsor, status` in that order and string values, preceded
  by the two comment lines:

  ```
  # Generated by `docassert projects` — do not edit.
  # The project.md anchors under documents/ are the source of truth.
  ```

  emitted as YAML without key sorting, UTF-8, LF, trailing newline. Registry
  freshness (§8.3) is byte-equality against this canonical form.
- **14.6 Multiple documents per kind.** Permitted. Each document is validated
  independently; profile completeness (§9) counts a kind complete when at
  least one qualifying document exists; the *latest* status report is the one
  with the greatest `period`.
- **14.7 Failure signalling.** A processor MUST fail its evaluation (non-zero
  exit or failing status) iff at least one blocking failure exists. Exact
  exit codes are implementation-defined.
- **14.8 Robustness.** A document whose frontmatter cannot be parsed produces
  a blocking `parse` failure for that document; an unknown check id in
  criteria produces a failure of that check. Neither crashes the evaluation.
- **14.9 Conformance reports.** For interchange and conformance testing, a
  processor MUST be able to emit a JSON report of the form
  `{"summary": {...}, "documents": {"<path>": [{"check_id", "passed",
  "blocking", "kind", "score", "detail"}, ...]}}`. Only `check_id`, `passed`,
  and `blocking` are normative; `detail` wording and `score` are not.


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
severity       blocking: always | once-proposed | never
               (once-proposed = advisory while status is draft)
```

## Appendix B — Reference implementation (non-normative)

[docassert](https://github.com/c4g-john/docassert) implements this
specification (`pip install docassert`), ships the standard kind library of
§7.2 as packaged defaults with local-override resolution (§3), and provides
the derived-status renderers of §10. A living conforming repository is
[pmo-as-code-pipeline](https://github.com/c4g-john/pmo-as-code-pipeline); a
starter is [pmo-as-code-template](https://github.com/c4g-john/pmo-as-code-template).

## Appendix C — Execution mapping (informative)

*Repository routing:* when project anchors carry the OPTIONAL `repo` field
(§5.1), a processor SHOULD route each project's Features and Stories to that
repository, and reconciliation within a repository SHOULD treat the union of
all projects mapped to it as in scope. An explicit target repository supplied
at invocation applies the whole plan to that repository unchanged.

This appendix documents how a repository's approved scope can drive an
execution tracker, as proven by the reference deployment. It is informative:
processors are not required to implement it, and none of it affects
conformance. It may be promoted to a normative profile in a future version
once a second consumer exists.

**The one-directional authority rule.** Scope flows documents → tracker;
execution state flows tracker → rendered status; nothing flows tracker →
documents. An item created directly in the tracker is not scope, and a closed
tracker item never modifies a document. Scope changes travel the same path as
any change: a reviewed pull request against the documents.

**The mapping** (GitHub terms; other trackers can mirror the shape):

| Standard concept | Tracker concept |
|---|---|
| Project (`PRJ-NNN-CODE`) | one project board, plus a `PMO Project` field on every item |
| Product requirement (`PR` item) with ≥ 1 linked story | a parent issue ("Feature") |
| User story (`US` item, `traces:` its PR item) | a sub-issue of its Feature |
| Acceptance criteria (`AC` items verifying the PR item) | a checklist in the Feature body |
| Code | pull requests closing Story issues |

**The gate.** A project enters the tracker only when its `user-story` document
is approved (§4.3) and every approved story traces to a resolvable product
requirement. Draft and proposed stories never reach the tracker; the board is
a commitment surface, not a backlog of ideas.

**Idempotency.** Every managed tracker item embeds its document item id as a
machine-readable marker (the reference implementation uses an HTML comment,
`<!-- docassert-bridge: RFH-US-001 -->`). The marker, not the title, is the
join key. Synchronization creates missing items, converges drifted titles and
bodies, and never deletes or reopens.

**Scope policing.** A reconciliation pass classifies every open tracker item:
*matched* (marker resolves to a current approved item), *unverified* (no
marker), or *orphaned* (marker resolves to an item that was removed or
demoted). Unverified and orphaned items are labelled and alerted, never
auto-closed; a human decides, and the honest fix for new scope is a documents
pull request. A non-zero exit from reconciliation makes CI itself the alarm.

**Delivery read-back.** Execution progress (closed stories per feature) and
the scope classification may be rendered beside the document-derived status.
Delivery figures MUST NOT alter the derived status of §10 in this mapping;
scope health and schedule health remain separate signals.

