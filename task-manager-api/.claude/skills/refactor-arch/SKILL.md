---
name: refactor-arch
description: Analyzes, audits, and refactors an entire backend codebase to MVC, agnostic of language/framework (Flask, Express, similar) — a full-codebase pass, not a git-diff review (use security-review for diffs). Use when the user mentions refactor to MVC, SQL injection, hardcoded secrets, God class, or shares backend source and asks what's wrong with it. Runs in three gated phases, pausing for confirmation before any code change.
---

# Refactor Arch

Turn a backend codebase — in any language or framework — into a well-structured
MVC application, safely. The skill never jumps straight to rewriting code: it
always analyzes first, reports what it found with hard evidence (file + line),
gets the user's explicit go-ahead, and only then refactors. This order matters
because the user is trusting you not to silently rewrite a system they depend
on based on a guess about what's wrong with it.

The workflow has three phases. Do not skip or reorder them, and do not
collapse the pause between Audit and Refactor even if the anti-patterns look
obvious — the user may have context you don't (a "hardcoded" key that's
actually a test fixture, a "God class" that's intentionally being retired
next sprint, etc.).

## Phase 1 — Analysis

Goal: understand what you're working with before judging it.

1. Identify the language(s) and framework(s) in use (check manifest files:
   `requirements.txt`/`pyproject.toml`, `package.json`, `go.mod`, `pom.xml`,
   etc., and the import/require statements in entrypoints).
2. Map the current file/module layout and how requests flow through it:
   entrypoint → routing → request handling → data access → response.
3. Classify the current architecture shape (see
   `references/analysis-heuristics.md` for the detection heuristics and the
   shape taxonomy — e.g. single-file monolith, fat-controller, fat-model,
   ad-hoc scripts with no layering, or already-MVC-ish-but-leaky).
4. Note the runtime/test entry points you'll need later to prove the
   refactor didn't break anything (how the app starts, how it's tested, what
   "it works" means for this project).

Output of this phase: a short summary (stack, layout, architecture shape,
how to run/verify the app). Don't present this as a deliverable on its own —
fold it into the Audit report's opening section.

## Phase 2 — Audit

Goal: produce an evidence-based, severity-ranked findings report — and stop.

1. Scan the codebase for the anti-patterns catalogued in
   `references/antipattern-catalog.md`. That file describes each anti-pattern
   by its **structural signal** (what the code does), not by language syntax,
   because the same smell shows up differently in Python, JavaScript, or
   anything else. Read it before scanning.
2. Optionally run `scripts/scan_signals.sh <project_root>` to get a fast,
   grep-based first pass of candidate locations (secrets, weak hashes, debug
   flags, string-built queries, bare excepts/catches, `print`/`console.log`
   debugging left in place). Treat every hit as a **candidate**, not a
   confirmed finding — the script over-triggers on purpose (e.g. it flags
   any `md5(` call, even a harmless cache-key hash). Read the surrounding
   code yourself and only report what's a genuine instance of the
   anti-pattern's structural signal.
3. For every confirmed finding, record: anti-pattern ID, severity, exact
   file path and line number(s), a one-line explanation of *why* it's a
   problem (impact, not just "this is bad practice"), and a short code
   excerpt as evidence.
4. Assemble the report using `references/audit-report-template.md`.
   Findings **must** be sorted by severity: CRITICAL, then HIGH, then
   MEDIUM, then LOW; within a severity, group by file.
5. Present the report to the user and stop. Literally end your turn asking
   the user to confirm which findings to act on (all of them, a subset, or
   "just show me — don't change anything yet"). Do not start Phase 3 in the
   same turn you deliver the audit, even if the user's original request was
   "audit and fix it" — confirmation must happen on the actual findings, not
   on the abstract idea of finding them, because a CRITICAL count of 6 reads
   very differently before and after the user has actually seen them.

## Phase 3 — Refactor

Goal: restructure toward MVC and prove the app still works, one confirmed
finding at a time.

1. Re-read `references/mvc-architecture-guidelines.md` for the target
   layout appropriate to the detected stack (Python/Flask, Node/Express, or
   the generalized layering if the framework is something else). MVC here
   means: **routes/controllers** handle HTTP in/out only, **services**
   (or a clearly-named business-logic layer) hold the actual business
   rules, and **models** own data access and persistence shape — nothing
   more.
2. For each finding the user confirmed, apply the matching transformation
   from `references/refactoring-playbook.md`. Each playbook entry has a
   before/after example — use it as a pattern to adapt, not a template to
   paste verbatim; match the project's existing naming and idioms.
3. Prefer small, verifiable steps over one giant rewrite: fix, then verify,
   then move to the next finding. This makes it obvious which change caused
   a regression if one appears.
4. After each meaningful change (and definitely at the end), validate the
   application still works using the entry points identified in Phase 1 —
   run the existing test suite if there is one, and otherwise start the app
   and exercise the affected endpoints/functions directly (e.g. `curl` a
   changed route, import and call a changed function). A refactor that
   "should still work" but was never actually run is not done.
5. **Before marking any finding "FIXED" in the summary, re-check the
   original recommendation action by action** — not just "did I touch this
   file". Some recommendations are composite: they list two or more
   distinct actions (e.g. "add authentication, AND add a role check before
   allowing the `role` field to change"; "encrypt the field at rest, AND
   stop logging it in plaintext"). A finding is "FIXED" only when **every**
   action in the recommendation was applied and verified. If a composite
   recommendation had only some of its actions applied, the correct status
   is **"PARTIALLY FIXED"**, with an explicit note naming exactly which
   action(s) are still missing — never round a partial fix up to "FIXED".
   This applies to any finding with a compound recommendation, not just
   authorization findings (see playbook #21 for the specific
   field-level-authorization case this rule was written for). When in
   doubt, re-read the finding's "Recommended fix" line from the Phase 2
   report verbatim and check off each clause it contains before writing
   the status.
6. Summarize what changed, referencing findings by ID and their status
   (FIXED or PARTIALLY FIXED, per the rule above), and flag anything you
   deliberately left alone (e.g. a LOW finding out of scope, or a finding
   that needs a decision only the user can make, like which secrets
   manager to adopt).

## Reference files

- `references/analysis-heuristics.md` — how to detect stack, layout, and
  architecture shape in Phase 1.
- `references/antipattern-catalog.md` — the full anti-pattern catalog,
  each entry with severity, language-agnostic structural signal, and
  concrete Python/Flask and Node/Express examples of what that signal looks
  like in practice.
- `references/audit-report-template.md` — the exact report structure and
  formatting rules for Phase 2, plus the confirmation prompt to end on.
- `references/mvc-architecture-guidelines.md` — target MVC layout and
  layering rules used in Phase 3.
- `references/refactoring-playbook.md` — transformation patterns with
  before/after code, one per anti-pattern in the catalog.
- `scripts/scan_signals.sh` — optional grep-based first-pass scanner for
  Phase 2 (candidates only, always verify manually before reporting).

Read a reference file when the phase it supports begins — don't front-load
all of them before you've even looked at the code.
