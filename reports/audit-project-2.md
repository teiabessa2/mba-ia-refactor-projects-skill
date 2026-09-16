# Architecture & Security Audit — ecommerce-api-legacy

## 1. Overview
- **Stack:** Node.js / Express 4.18 + `sqlite3` (in-memory, no ORM). No test framework, no `test` script in `package.json`.
- **Architecture shape:** **Single-file monolith / God module.** `app.js` only wires up Express and `AppManager`; every route, every DB query, and every business rule (payment authorization, enrollment, audit logging, admin reporting) lives inside one class (`AppManager.js`) with no router/controller/service/model separation at all.
- **Files scanned:** `src/app.js`, `src/AppManager.js`, `src/utils.js` (3 files, ~165 lines total — full read).
- **How to verify changes:** No test suite exists (`package.json` has no `test` script or test dependency). Verification was manual: `npm start`, then exercise the three routes with the requests already provided in `api.http`.

## 2. Findings summary

| # | Severity | Anti-pattern | File | Line(s) |
|---|----------|--------------|------|---------|
| 1 | CRITICAL | Hardcoded credentials/secrets (C2) | utils.js | 2-4 |
| 2 | CRITICAL | Weak/absent password hashing — homemade "encryption" (C3) | utils.js | 17-23 (used at AppManager.js:68) |
| 3 | CRITICAL | Missing authorization on admin financial report (C6) | AppManager.js | 80-129 |
| 4 | CRITICAL | Missing authorization on destructive user-delete endpoint (C6) | AppManager.js | 131-137 |
| 5 | HIGH | God Class/Module (H3) | AppManager.js | whole file |
| 6 | HIGH | Business logic embedded in controller (H4) | AppManager.js | 28-78 |
| 7 | HIGH | N+1 query pattern (H5) | AppManager.js | 89-127 |
| 8 | HIGH | Manual async fan-in counters / unchecked errors (H6) | AppManager.js | 80-129 |
| 9 | MEDIUM | Generic/swallowed error handling, no logging (M2) | AppManager.js | 38, 41, 48, 51, 55, 84, 104-106 |
| 10 | MEDIUM | Callback hell (M3) | AppManager.js | 28-78, 89-127 |
| 11 | LOW | Missing pagination (L1) | AppManager.js | 80-129 |
| 12 | LOW | Print debugging instead of a logger (L2) | AppManager.js, utils.js, app.js | 45; 13; 13 |

## 3. Findings detail

### CRITICAL

#### [C2] Hardcoded credentials and secrets
- **File:** `utils.js:2-4`
- **Evidence:**
  ```javascript
  const config = {
      dbUser: "admin_master",
      dbPass: "senha_super_secreta_prod_123",
      paymentGatewayKey: "pk_live_1234567890abcdef",
      ...
  };
  ```
- **Why it matters:** `paymentGatewayKey` looks like a **live** payment-gateway key (`pk_live_...`) baked directly into source. Anyone with repo access gets working production payment credentials — and it's made worse by finding #12 (L2): this exact key is printed to stdout on every checkout (`AppManager.js:45`), so even log access alone leaks it.
- **Recommended fix:** Load all three values from environment variables with no baked-in default — see refactoring-playbook.md #2.
- **Status:** FIXED — `dbUser`/`dbPass`/`smtpUser` removed entirely (confirmed dead, never consumed anywhere in the app). `paymentGatewayKey` and a new `adminApiKey` now load from `process.env` via `src/config/index.js`, no hardcoded fallback.

#### [C3] Weak/absent password hashing — homemade "encryption"
- **File:** `utils.js:17-23`, called at `AppManager.js:68`
- **Evidence:**
  ```javascript
  function badCrypto(pwd) {
      let hash = "";
      for(let i = 0; i < 10000; i++) {
          hash += Buffer.from(pwd).toString('base64').substring(0, 2);
      }
      return hash.substring(0, 10);
  }
  ```
  ```javascript
  let hash = badCrypto(p || "123456");
  this.db.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [u, e, hash], ...);
  ```
- **Why it matters:** this isn't hashing, it's repeated base64 encoding of the same input truncated to 10 chars — fully reversible with no secret, and the loop is pure theater (it always re-encodes the identical 2-char prefix). Every "password" a customer submits during checkout is stored as a trivially-decodable string. It's also silently used with a **hardcoded default password (`"123456"`)** whenever the checkout call omits `pwd` entirely — every such auto-created account shares the same guessable password.
- **Recommended fix:** Hash on write with `bcrypt`/`argon2`, drop the hardcoded default — see refactoring-playbook.md #3.
- **Status:** FIXED — `badCrypto` deleted, replaced with `bcryptjs` (`services/checkout.service.js`), 12 salt rounds.

#### [C6] Missing authorization — admin financial report
- **File:** `AppManager.js:80-129`
- **Evidence:**
  ```javascript
  app.get('/api/admin/financial-report', (req, res) => {
      let report = [];
      this.db.all("SELECT * FROM courses", [], (err, courses) => {
  ```
- **Why it matters:** despite `/admin/` in the path, there is no auth check anywhere in this handler or its route registration. Anyone who can reach the server gets total revenue per course and a per-student breakdown of who paid what — no credentials required.
- **Recommended fix:** Add an auth/role check before the handler runs — see refactoring-playbook.md #5 / #6.
- **Status:** FIXED — protected by a static admin-API-key middleware (`middlewares/adminAuth.js`), checked against `x-admin-api-key`.

#### [C6] Missing authorization — destructive user-delete endpoint
- **File:** `AppManager.js:131-137`
- **Evidence:**
  ```javascript
  app.delete('/api/users/:id', (req, res) => {
      let id = req.params.id;
      this.db.run("DELETE FROM users WHERE id = ?", [id], (err) => {
          res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
      });
  });
  ```
- **Why it matters:** any caller can delete any user by guessing/incrementing an ID, with zero auth check — and the response message itself admits the delete corrupts related data (orphaned `enrollments`/`payments` rows), so this is a destructive, unauthenticated endpoint with no data-integrity handling either.
- **Recommended fix:** Add an auth/role check, and decide the intended behavior for related rows (cascade delete vs. soft delete) — see refactoring-playbook.md #5 / #6.
- **Status:** FIXED — same admin-API-key middleware applied; the delete now cascades to the user's enrollments/payments (`services/users.service.js`) instead of leaving them orphaned, and returns `204`.

### HIGH

#### [H3] God Class/Module
- **File:** `AppManager.js` (whole file)
- **Evidence:** one class owns schema creation and seeding for 5 unrelated tables (`users`, `courses`, `enrollments`, `payments`, `audit_logs`) **and** every route's HTTP handling **and** every raw DB query — there's no router, controller, service, or model layer anywhere in the project.
- **Why it matters:** you can't describe this file's responsibility in one sentence without "and". Any change (a new payment rule, a new admin report) risks touching unrelated code, and nothing here is testable without spinning up Express and a live DB connection.
- **Recommended fix:** Split into routes/controllers, a service layer for checkout logic, and per-entity models — see refactoring-playbook.md #4 / mvc-architecture-guidelines.md.
- **Status:** FIXED — split into `config/`, `db/`, `models/` (one file per entity: users, courses, enrollments, payments, auditLogs, reports), `services/`, `controllers/`, `routes/`, `middlewares/`.

#### [H4] Business logic embedded in the controller (checkout)
- **File:** `AppManager.js:28-78`
- **Evidence:**
  ```javascript
  console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
  let status = cc.startsWith("4") ? "PAID" : "DENIED";
  if (status === "DENIED") return res.status(400).send("Pagamento recusado");
  ```
- **Why it matters:** the route handler itself decides payment approval (`cc.startsWith("4")`), creates users, records enrollments, records payments, and writes audit logs — a full business workflow with no service/use-case layer. None of this can be reused by a background job or tested without an HTTP request and a live DB.
- **Recommended fix:** Extract a `CheckoutService` that orchestrates user lookup/creation, payment authorization, enrollment, and audit logging — the route handler should only parse the request and call it — see refactoring-playbook.md #4.
- **Status:** FIXED — extracted into `services/checkout.service.js`; `controllers/checkout.controller.js` only parses the request body and shapes the response.

#### [H5] N+1 query pattern
- **File:** `AppManager.js:89-127`
- **Evidence:**
  ```javascript
  courses.forEach(c => {
      this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], (err, enrollments) => {
          enrollments.forEach(enr => {
              this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], (err, user) => {
                  this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => {
  ```
- **Why it matters:** for C courses and E total enrollments, this issues `1 + C + E + E` queries instead of a handful of joins — fine with the 2 seeded courses, but response time and DB load scale linearly (worse) with catalog size and enrollment volume.
- **Recommended fix:** Replace with a single `JOIN` query across `courses`/`enrollments`/`users`/`payments`, aggregated in application code — see refactoring-playbook.md #7.
- **Status:** FIXED — replaced with a single `JOIN` query (`models/reports.model.js`), aggregated per course in `services/reports.service.js`.

#### [H6] Manual async fan-in counters with unchecked errors
- **File:** `AppManager.js:80-129`
- **Evidence:**
  ```javascript
  let coursesPending = courses.length;
  ...
  enrollments.forEach(enr => {
      this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], (err, user) => {
          this.db.get("SELECT amount, status FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => {
              // err is never checked in either of these two nested calls
              ...
              enrPending--;
              if (enrPending === 0) { report.push(courseData); coursesPending--; if (coursesPending === 0) res.json(report); }
  ```
- **Why it matters:** this is the exact "manually counting completed async callbacks instead of `Promise.all`" pattern — completion is detected by decrementing shared counters across nested callbacks, and the two innermost `err` parameters are never checked. If any single query errors (a locked DB, a bad row), `user`/`payment` become `undefined`, the counter still decrements as if it succeeded, and depending on timing the response can be sent with silently wrong data, sent twice, or never sent at all (hung request) if the callback that fires last does throw.
- **Recommended fix:** Replace the whole handler with `Promise.all` over promisified DB calls, or a single joined query (this overlaps with H5's fix) — see refactoring-playbook.md #7.
- **Status:** FIXED — resolved as a side effect of the H5 fix: `db/database.js` promisifies `run`/`get`/`all`, and `reports.service.js` uses `Promise.all` plus a single joined query instead of any manual counters.

### MEDIUM

#### [M2] Generic/swallowed error handling without logging
- **File:** `AppManager.js` — e.g. lines 38, 41, 48, 51, 55, 84, and the fully-unchecked `err` at 104, 106
- **Evidence:**
  ```javascript
  if (err) return res.status(500).send("Erro DB");
  ```
- **Why it matters:** every DB error in this file is either turned into a generic "Erro DB" string with the original exception thrown away, or — in the financial-report nested calls — not checked at all. When something breaks in production, there is no trail (no `console.error`, no logger, nothing) to diagnose what actually failed.
- **Recommended fix:** Log the original error (structured logger, not `console.log`) before responding, and check every `err` parameter, including the nested ones in financial-report — see refactoring-playbook.md #8.
- **Status:** FIXED — centralized in `middlewares/errorHandler.js`, which logs every error via `pino` before responding; controllers pass errors to it with `next(err)` instead of swallowing them.

#### [M3] Callback hell
- **File:** `AppManager.js:28-78` (checkout), `89-127` (financial-report)
- **Evidence:** checkout nests `db.get` → `db.get` → (`db.run` → `db.run` → `db.run` → `res.json`) up to 6 levels deep; financial-report nests `forEach` → `db.all` → `forEach` → `db.get` → `db.get` up to 5 levels deep.
- **Why it matters:** control flow and error handling are hard to follow at this depth, and every additional step (e.g. adding an email-receipt step to checkout) means one more nesting level rather than one more line.
- **Recommended fix:** Convert to `async`/`await` over promisified `sqlite3` calls once the logic is extracted into a service — see refactoring-playbook.md #7.
- **Status:** FIXED — `db/database.js` promisifies the sqlite3 driver; both flows are flat `async`/`await` in their respective services.

### LOW

#### [L1] Missing pagination
- **File:** `AppManager.js:80-129`
- **Evidence:** `/api/admin/financial-report` returns every course, every enrollment, and every student with no limit/offset.
- **Why it matters:** fine with 2 seeded courses; unbounded response size and query cost as the catalog and enrollment count grow.
- **Recommended fix:** Add `page`/`size` (or cursor) parameters, capped at a sane max.
- **Status:** FIXED — `page`/`size` query params added, capped at 100, response now includes `{report, page, size, total}`.

#### [L2] Print debugging instead of a structured logger
- **File:** `AppManager.js:45`, `utils.js:13`, `app.js:13`
- **Evidence:**
  ```javascript
  console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
  ```
- **Why it matters:** no log levels, no way to filter or redirect without a code change — and in this specific instance (`AppManager.js:45`) it's also actively leaking the hardcoded payment key into logs on every checkout (compounds finding C2).
- **Recommended fix:** Replace with a structured logger (e.g. `pino`/`winston`) with levels.
- **Status:** FIXED — replaced with `pino` (`utils/logger.js`); the payment key is no longer logged anywhere.

## 4. Out of scope / needs a decision
- `totalRevenue` (`utils.js:10`) is exported and imported into `AppManager.js:2` but never referenced anywhere — dead code. Removed during the refactor rather than re-hosted.
- `globalCache` (`utils.js:9`, written via `logAndCache`) is module-level mutable state, but it's only ever written, never read back anywhere in the codebase. Removed during the refactor.
- No pre-existing test suite, so all Phase 3 verification was manual (`npm start` + the requests in `api.http`, extended with `curl` for the new auth/pagination behavior).
- **No auth system existed at all before this refactor.** Per the playbook's own guidance ("if the project has no auth system at all yet, that's a decision for the user, not something to pick unilaterally"), this was surfaced explicitly before Phase 3. User selected a static admin API key (env-driven, checked via middleware) over JWT-with-roles or HTTP Basic Auth.

---

This audit found 12 findings (4 CRITICAL, 4 HIGH, 2 MEDIUM, 2 LOW).

**Resolution:** user selected "fix everything, in severity order." All 12 findings were fixed and verified against a running instance of the application (checkout success/denied/404, paginated financial report before/after a cascading delete, and 401s for the two admin-protected endpoints without the API key).
