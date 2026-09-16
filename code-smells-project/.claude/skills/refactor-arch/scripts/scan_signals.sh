#!/usr/bin/env bash
# First-pass, language-agnostic grep scan for refactor-arch Phase 2 (Audit).
#
# This finds CANDIDATES, not confirmed findings. It intentionally
# over-triggers (e.g. it flags every md5() call, even a harmless cache key).
# Read the surrounding code for each hit and only report genuine instances
# of the anti-pattern's structural signal from antipattern-catalog.md.
#
# Usage: scan_signals.sh <project_root>

set -euo pipefail

ROOT="${1:-.}"
EXCLUDE_DIRS='node_modules|\.git|venv|\.venv|dist|build|__pycache__|\.next|vendor'

grep_project() {
  local pattern="$1"
  grep -rniE --color=never "$pattern" "$ROOT" \
    --include='*.py' --include='*.js' --include='*.ts' --include='*.mjs' \
    --include='*.rb' --include='*.php' --include='*.go' --include='*.java' \
    2>/dev/null | grep -vE "$EXCLUDE_DIRS" || true
}

section() {
  echo ""
  echo "=== $1 ==="
}

section "C1 candidates: SQL-like strings built with concatenation/interpolation"
grep_project '(execute|query|raw)\s*\(.*(SELECT|INSERT|UPDATE|DELETE).*(\+|%s|f"|f'"'"'|\.format\(|\$\{)'
grep_project '(SELECT|INSERT|UPDATE|DELETE)[^"'"'"']*"\s*\+'

section "C2 candidates: hardcoded secrets/credentials (by variable name)"
grep_project '(secret|password|pass|pwd|senha|api[_-]?key|apikey|token|credential)[a-z0-9_]*["'"'"']?\]?[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"']{4,}["'"'"']'

section "C2 candidates: hardcoded secrets (by value shape — catches keys named anything, e.g. paymentGatewayKey)"
grep_project '["'"'"'](pk_live_|sk_live_|pk_test_|sk_test_|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-|AIza[0-9A-Za-z_-]{20,})'

section "C3 candidates: weak hashing / plaintext password comparison"
grep_project '\b(md5|sha1)\s*\('
grep_project '(senha|password)\s*==\s*'

section "C4 candidates: hand-built tokens (base64/concat of user data)"
grep_project '(b64encode|base64\.b64encode|Buffer\.from).*(user|email|id)'

section "C5 candidates: dynamic execution of caller-supplied code/SQL"
grep_project '\b(eval|exec)\s*\('
grep_project 'cursor\.execute\(\s*(query|sql|dados\[)'

section "H1 candidates: debug mode flags"
grep_project '(debug\s*=\s*True|DEBUG\s*=\s*True|NODE_ENV.*development)'

section "H2 candidates: commonly-deprecated calls (verify against installed version)"
grep_project '\butcnow\(\)|new Buffer\(|\brequire\([\x27"]request[\x27"]\)'

section "M4 candidates: sensitive fields returned from serialization"
grep_project '["'"'"'](password|senha|password_hash|senha_hash|secret|token)["'"'"']\s*:\s*(self\.|row\[|user\.|usuario\[|this\.)'

section "M2 candidates: generic exception handling"
grep_project 'except\s*:|except\s+Exception'
grep_project 'catch\s*\(\s*\w*\s*\)\s*\{\s*\}'

section "L2 candidates: print/console debugging instead of a logger"
grep_project '\bprint\(|console\.(log|error|warn)\('

section "L1 hint: list endpoints/functions with no limit/offset/page param nearby"
grep_project 'SELECT \* FROM \w+"?\s*\)'

echo ""
echo "--- Manual-only checks (not reliably greppable) ---"
echo "C3 Weak/absent password hashing: absence of hashing is a negative signal"
echo "  grep can't reliably catch. Check every INSERT/UPDATE writing a"
echo "  password/senha column and every login comparison for a call into a"
echo "  hashing library (bcrypt/scrypt/argon2/werkzeug.security) around it."
echo "C6 Missing authentication/authorization: absence of an auth check is a"
echo "  negative signal grep can't reliably catch. For every route that"
echo "  deletes/resets data, runs arbitrary queries, or touches another"
echo "  user's records, check whether any auth middleware/decorator/session"
echo "  check actually runs before the handler body."
echo "H3 God Class/Module: open each file under 'models'/'controllers' and check"
echo "  whether it spans more than one unrelated domain entity."
echo "H4 Business logic in controllers/models: read each handler for workflow"
echo "  logic or side effects beyond request parsing / persistence."
echo "H5 N+1 queries: look for a query call inside a loop body iterating over a"
echo "  previous query's results."
echo "H6 Race conditions: look for module-level mutable state read/written from"
echo "  concurrent or async handlers without a lock."
echo "M1 Duplicated validation: diff the validation blocks of create vs. update"
echo "  handlers for the same entity."
echo "M3 Callback hell: look for callbacks nested more than ~2 levels deep."
