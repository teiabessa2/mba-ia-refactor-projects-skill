# Audit Report Template (Phase 2)

Use this structure exactly for the report you hand back to the user at the
end of Phase 2. The point of a fixed structure is that the user can scan
straight to severity and location without re-reading prose each time.

## Ordering rule

Findings are sorted **CRITICAL → HIGH → MEDIUM → LOW**. Within a severity,
group by file (so a reader fixing one file sees everything relevant to it
together). Never interleave severities to match file order — severity
order wins.

## Structure

```markdown
# Architecture & Security Audit — <project name>

## 1. Overview
- **Stack:** <language, framework, version if known>
- **Architecture shape:** <one of the Phase 1 taxonomy labels> — <one-sentence justification>
- **Files scanned:** <count or list, if the project is small enough to enumerate>
- **How to verify changes:** <test command, or "no test suite found — manual
  endpoint exercise only">

## 2. Findings summary

| # | Severity | Anti-pattern | File | Line(s) |
|---|----------|--------------|------|---------|
| 1 | CRITICAL | SQL Injection (C1) | models.py | 24 |
| 2 | CRITICAL | Hardcoded secret (C2) | app.py | 7 |
| ... | | | | |

## 3. Findings detail

### CRITICAL

#### [C1] SQL Injection via string-built query
- **File:** `models.py:24`
- **Evidence:**
  ```python
  cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
  ```
- **Why it matters:** <impact specific to this instance — what data, what
  access an attacker gains, not the generic catalog description verbatim>
- **Recommended fix:** <one line pointing at the matching playbook entry,
  e.g. "Parameterize the query — see refactoring-playbook.md #1">

(repeat for every CRITICAL finding, then HIGH, then MEDIUM, then LOW,
using the same sub-structure)

## 4. Out of scope / needs a decision
List anything you noticed but couldn't classify confidently, or that needs
a call only the user can make (e.g. "which secrets manager does this org
already use?" or "is this admin endpoint actually meant to be public?").
Don't silently drop these — an audit that only reports what's easy to
classify understates its own uncertainty.
```

## Rules for filling it in

- **Every finding needs a real file path and line number** — if you can't
  point at exact evidence, it's not a finding yet, it's a hunch; keep
  investigating or move it to section 4.
- **Quote the actual code**, don't paraphrase it — the user needs to be
  able to verify your claim by looking at the same lines.
- **"Why it matters" must be specific to this instance**, not a copy-paste
  of the catalog's generic description. "This leaks the admin session
  signing key" is useful; "hardcoded secrets are bad practice" is not.
- **Don't invent findings to hit a quota.** If a project genuinely has 3
  findings, report 3. Padding a report with low-value nitpicks to look
  thorough erodes trust in the CRITICAL/HIGH findings that actually matter.
- **Don't fix anything while writing this report.** Even a "quick" one-line
  fix violates the phase boundary — the whole point of Phase 2 is that
  nothing changes before the user has seen the full picture and agreed.

## End every audit with this (verbatim intent, adapt wording)

```
This audit found <N> findings (<Ccount> CRITICAL, <Hcount> HIGH, <Mcount>
MEDIUM, <Lcount> LOW). I haven't changed anything yet.

How would you like to proceed?
- Fix everything, in severity order
- Fix only CRITICAL and HIGH
- Pick specific findings by number
- Just wanted the report — hold off on changes
```

Stop your turn there. Do not begin Phase 3 until the user responds.
