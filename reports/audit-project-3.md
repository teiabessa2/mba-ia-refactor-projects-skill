# Architecture & Security Audit — task-manager-api

## 1. Overview
- **Stack:** Python 3 / Flask 3.0.0, Flask-SQLAlchemy 3.1.1, SQLite (`tasks.db`)
- **Architecture shape:** **Leaky MVC** — `models/`, `routes/`, `services/`, `utils/` already exist as separate folders, but request validation, business rules (overdue logic, stats aggregation), and response shaping live directly in the route handlers rather than a service layer; the model layer defines rules (`is_overdue`, `validate_status`, `validate_priority`) that are never actually called from the routes; the one service (`NotificationService`) is never instantiated anywhere.
- **Files scanned:** `app.py`, `database.py`, `seed.py`, `models/{task,user,category}.py`, `routes/{task,user,report}_routes.py`, `services/notification_service.py`, `utils/helpers.py` (11 files)
- **How to verify changes:** No test suite found. Verification relied on starting the app (`python seed.py && python app.py`) and manually exercising endpoints (`curl`) after each change.

## 2. Findings summary

| # | Severity | Anti-pattern | File | Line(s) |
|---|----------|--------------|------|---------|
| 1 | CRITICAL | Hardcoded secret — Flask `SECRET_KEY` (C2) | app.py | 13 |
| 2 | CRITICAL | Hardcoded secret — SMTP password (C2) | services/notification_service.py | 10 |
| 3 | CRITICAL | Weak password hashing — MD5 (C3) | models/user.py | 29, 32 |
| 4 | CRITICAL | Forged/unsigned auth token (C4) | routes/user_routes.py | 210 |
| 5 | CRITICAL | Missing authentication/authorization on sensitive endpoints (C6) | routes/task_routes.py, routes/user_routes.py, routes/report_routes.py | see detail |
| 6 | CRITICAL | Password hash exposed in API responses, escalated by C3 (M4) | models/user.py, routes/user_routes.py | 21; 86, 129, 209 |
| 7 | HIGH | Debug mode enabled (H1) | app.py | 34 |
| 8 | HIGH | Deprecated API — `datetime.utcnow()` (H2) | multiple files | see detail |
| 9 | HIGH | God module by domain sprawl — Category CRUD inside "reports" blueprint (H3) | routes/report_routes.py | 157–223 |
| 10 | HIGH | Business logic embedded in controllers (H4) | routes/task_routes.py, routes/user_routes.py, routes/report_routes.py | see detail |
| 11 | HIGH | N+1 query pattern (H5) | routes/task_routes.py, routes/report_routes.py | 41–57; 55–68 |
| 12 | MEDIUM | Bypassed centralized logic — `Task.is_overdue()` never called, reimplemented 6x (M1) | routes/task_routes.py, routes/user_routes.py, routes/report_routes.py | see detail |
| 13 | MEDIUM | Bypassed centralized logic — `Task.validate_status/validate_priority` and `process_task_data()` never called (M1) | models/task.py, utils/helpers.py, routes/task_routes.py | 38-48; 57-108; 110-114, 181-184 |
| 14 | MEDIUM | Bypassed centralized logic — `format_date`/`calculate_percentage` imported but unused (M1) | routes/report_routes.py | 7, 67, 71, 151 |
| 15 | MEDIUM | Generic exception handling without logging (M2) | routes/task_routes.py, routes/report_routes.py, utils/helpers.py | 62,137,204,236; 186,207,221; 46,49,88 |
| 16 | LOW | Missing pagination on list endpoints (L1) | routes/task_routes.py, routes/user_routes.py, routes/report_routes.py | 12, 240; 10; 158 |
| 17 | LOW | print() used instead of structured logger (L2) | routes/task_routes.py, routes/user_routes.py, services/notification_service.py, utils/helpers.py, seed.py | see detail |

## 3. Findings detail

### CRITICAL

#### [C2] Hardcoded Flask secret key
- **File:** `app.py:13`
```python
app.config['SECRET_KEY'] = 'super-secret-key-123'
```
- **Why it matters:** This key signs Flask's session cookies. Since it's committed to source, anyone with repo access can forge signed session data for this deployment.
- **Recommended fix:** Load from environment variable — see refactoring-playbook.md.

#### [C2] Hardcoded SMTP credentials
- **File:** `services/notification_service.py:10`
```python
self.email_password = 'senha123'
```
- **Why it matters:** A real Gmail account's password is in source. Even though this service is never instantiated anywhere in the app (dead code today), the credential is still live and exposed to anyone with repo read access — see section 4 for the "is this feature meant to be wired up?" question.
- **Recommended fix:** Move to environment variable / secrets manager; rotate this credential since it's already been committed.

#### [C3] Weak password hashing (MD5)
- **File:** `models/user.py:29,32`
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
...
return self.password == hashlib.md5(pwd.encode()).hexdigest()
```
- **Why it matters:** MD5 is unsalted and fast — a leaked `tasks.db` lets an attacker recover every user's real password via rainbow tables/brute force in seconds per password.
- **Recommended fix:** Use `werkzeug.security.generate_password_hash`/`check_password_hash` (already a Flask dependency) — see refactoring-playbook.md.

#### [C4] Forged/unsigned authentication token
- **File:** `routes/user_routes.py:210`
```python
'token': 'fake-jwt-token-' + str(user.id)
```
- **Why it matters:** This is a predictable string built from the user's own ID — anyone can construct `fake-jwt-token-1` and impersonate user 1 (including an admin) without ever knowing a password. Combined with finding #5 (no route actually validates this token), authentication is effectively decorative right now.
- **Recommended fix:** Issue a real signed token (JWT with the app's secret, or a server-side session) and require it on protected routes — see refactoring-playbook.md.

#### [C6] Missing authentication/authorization on sensitive endpoints
- **Files:**
  - `routes/task_routes.py:225-238` — `DELETE /tasks/<id>`
  - `routes/user_routes.py:92-132` — `PUT /users/<id>` (can silently set `role: 'admin'`, no check on who's calling)
  - `routes/user_routes.py:134-151` — `DELETE /users/<id>` (also cascades deletes to that user's tasks)
  - `routes/report_routes.py:167-223` — `POST/PUT/DELETE /categories`
- **Evidence (representative):**
```python
@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    ...
    if 'role' in data:
        if data['role'] not in ['user', 'admin', 'manager']:
            return jsonify({'error': 'Role inválido'}), 400
        user.role = data['role']   # no check that the caller is even authenticated
```
- **Why it matters:** There is a `/login` endpoint, but no route anywhere checks the returned token (confirmed by grep — no auth middleware/decorator exists in the codebase). Any unauthenticated caller can delete any task, delete any user (and their tasks), or promote themselves to admin via `PUT /users/<id>`.
- **Recommended fix:** Add an auth-required decorator/middleware that validates the token (once it's a real one, see C4) and apply it to every mutating route; add a role check for admin-only fields like `role`.

#### [M4, escalated to CRITICAL by C3] Password hash returned in API responses
- **File:** `models/user.py:21` (`to_dict()`), exercised at `routes/user_routes.py:86` (create), `:129` (update), `:209` (login)
```python
def to_dict(self):
    return {
        ...
        'password': self.password,
        ...
    }
```
- **Why it matters:** Every `POST /users`, `PUT /users/<id>`, and `/login` response includes the user's password hash. Because that hash is MD5 (C3), the response *is* the crackable credential, not just verification material — per the catalog this escalates M4 from MEDIUM to CRITICAL.
- **Recommended fix:** Strip `password` from `to_dict()` entirely; never serialize credential material — see refactoring-playbook.md.

---

### HIGH

#### [H1] Debug mode enabled in the entrypoint
- **File:** `app.py:34`
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```
- **Why it matters:** Unconditional debug mode on a host bound to `0.0.0.0` exposes Werkzeug's interactive debugger to the network — a known path to remote code execution if reached.
- **Recommended fix:** Gate behind an environment variable defaulting to `False`.

#### [H2] Deprecated API usage — `datetime.utcnow()`
- **Files:** `models/task.py:15,16,52`; `models/user.py:14`; `routes/task_routes.py:31,72,215,285`; `routes/user_routes.py:172`; `routes/report_routes.py:35,42,45,71,133`; `services/notification_service.py:35`; `utils/helpers.py:38`; `seed.py` (multiple)
- **Why it matters:** `datetime.utcnow()` is deprecated as of Python 3.12 in favor of `datetime.now(timezone.utc)` — it returns a naive datetime that silently loses timezone info, and every comparison against `due_date` in this codebase inherits that ambiguity.
- **Recommended fix:** Replace with `datetime.now(timezone.utc)` project-wide (mechanical, low-risk change) — see refactoring-playbook.md.

#### [H3] Category CRUD embedded in the "reports" blueprint
- **File:** `routes/report_routes.py:157-223`
- **Why it matters:** `report_bp` mixes read-only reporting (`/reports/summary`, `/reports/user/<id>`) with full CRUD for an unrelated domain entity (`/categories` create/update/delete). A reader can't describe this file's responsibility in one sentence, and category logic is now scattered outside where task/category-owning code would expect it.
- **Recommended fix:** Move `/categories/*` routes into their own blueprint/controller.

#### [H4] Business logic embedded in controllers
- **Files:** `routes/task_routes.py` (title/status/priority validation inline in `create_task`/`update_task`, lines 96-114 & 166-184; overdue computation inline, lines 30-39, 71-80, 283-287; stats aggregation inline, lines 273-299), `routes/report_routes.py` (full report aggregation inline, lines 12-224), `routes/user_routes.py` (email/password validation inline, lines 61-65, 106-116)
- **Why it matters:** With no service layer actually in use, every business rule (what counts as overdue, what's a valid status transition, how completion rate is computed) lives only inside HTTP handlers — it can't be reused by a background job or tested without spinning up a Flask request.
- **Recommended fix:** Extract into a service layer (`services/task_service.py`, `services/report_service.py`, etc.) called by thin controllers — see refactoring-playbook.md.

#### [H5] N+1 query pattern
- **File:** `routes/task_routes.py:41-57` (inside `get_tasks`)
```python
for t in tasks:
    ...
    if t.user_id:
        user = User.query.get(t.user_id)   # one query per task
    if t.category_id:
        cat = Category.query.get(t.category_id)   # one query per task
```
- **File:** `routes/report_routes.py:55-68` (inside `summary_report`)
```python
for u in users:
    user_tasks = Task.query.filter_by(user_id=u.id).all()   # one query per user
```
- **Why it matters:** `GET /tasks` issues up to `2N+1` queries for N tasks; `/reports/summary` issues `N+1` queries for N users. Fine with the seeded 10 tasks/3 users, but scales linearly and will slow down badly with real data volume.
- **Recommended fix:** Use SQLAlchemy eager loading (`joinedload`) or a single aggregate query instead of per-item lookups — see refactoring-playbook.md.

---

### MEDIUM

#### [M1] `Task.is_overdue()` defined but bypassed — reimplemented 6 times, already drifting
- **Canonical method:** `models/task.py:50-60`
- **Reimplemented at:** `routes/task_routes.py:30-39` (in `get_tasks`), `:71-80` (in `get_task`), `:283-287` (in `task_stats`); `routes/user_routes.py:171-180` (in `get_user_tasks`); `routes/report_routes.py:34-37` (in `summary_report`), `:132-135` (in `user_report`)
- **Why it matters:** Six independent copies of the same overdue rule. If the rule ever changes (e.g. adding a grace period), five of the six call sites won't get the fix — this is the exact "bypassed utility" pattern the catalog warns about.
- **Recommended fix:** Delete the duplicated inline logic, call `task.is_overdue()` everywhere.

#### [M1] `Task.validate_status`/`validate_priority` and `utils.helpers.process_task_data` defined but bypassed
- **Files:** `models/task.py:38-48`, `utils/helpers.py:57-108`, reimplemented inline in `routes/task_routes.py:110-114` (create) and `:181-184` (update)
- **Why it matters:** A full validate-and-normalize helper (`process_task_data`) already exists and covers title/status/priority/due_date/tags — but `create_task`/`update_task` reimplement the same checks by hand instead of calling it, so the two entry points can drift independently.
- **Recommended fix:** Either delete the unused helpers or route `create_task`/`update_task` through them — pick one source of truth.

#### [M1] `format_date`/`calculate_percentage` imported but never invoked
- **File:** `routes/report_routes.py:7` (import), `:67` and `:151` (percentage computed inline instead: `round((done/total)*100, 2)`), `:71` (date formatted inline instead: `str(datetime.utcnow())`)
- **Why it matters:** Small, but it's the same signal — a shared utility built for exactly this purpose sits unused while call sites hand-roll the same calculation.
- **Recommended fix:** Call the existing helpers, or remove them if the format truly needs to differ.

#### [M2] Generic exception handling without logging
- **Files:** `routes/task_routes.py:62` (bare `except:` swallowing `get_tasks` failures with zero record), `:137,204` (bare `except:` on date parsing), `:236` (bare `except:` on delete); `routes/report_routes.py:186,207,221` (bare `except:` on category create/update/delete); `utils/helpers.py:46,49,88` (bare `except:` in `parse_date`/`process_task_data`)
```python
try:
    tasks = Task.query.all()
    ...
except:
    return jsonify({'error': 'Erro interno'}), 500
```
- **Why it matters:** These catch-alls discard the exception entirely — no `print`, no logger, nothing. When `GET /tasks` returns a 500 in production, there is no trail at all to find out why.
- **Recommended fix:** At minimum log `str(e)` server-side (ideally via a real logger, see L2) before returning the generic response.

---

### LOW

#### [L1] Missing pagination on list endpoints
- **Files:** `routes/task_routes.py:12` (`GET /tasks`), `:240` (`GET /tasks/search`); `routes/user_routes.py:10` (`GET /users`); `routes/report_routes.py:158` (`GET /categories`)
- **Why it matters:** All four return every row unconditionally. Fine at today's 10 seeded tasks; unbounded at real scale.
- **Recommended fix:** Add `page`/`per_page` query params using SQLAlchemy's `.paginate()`.

#### [L2] `print()` used instead of a structured logger
- **Files:** `routes/task_routes.py:149,153,219,234`; `routes/user_routes.py:83,89,147`; `services/notification_service.py:21,24`; `utils/helpers.py:39,41`; `seed.py:93-96`
- **Why it matters:** No log level, no way to filter or redirect without a code change — noisy, unsearchable production output.
- **Recommended fix:** Replace with Python's `logging` module, configured once in `app.py`.

## 4. Out of scope / needs a decision
- **`NotificationService` is dead code.** It's fully implemented (`notify_task_assigned`, `notify_task_overdue`) but never instantiated or called from any route — assigning a task to a user or a task going overdue triggers no notification today. Worth asking: should this be wired up (e.g. called from `create_task`/`update_task` when `user_id` changes), or removed along with its hardcoded credential (finding #2)? I didn't assume either way.
- **`User.is_admin()`** is defined but never called — ties into finding #5 (no role check anywhere). Once real auth is added, this is the natural place to check admin-only actions.
- **Whether `/health` and `/` need auth** — left these alone; they're read-only and low-value, consistent with the catalog's guidance to use judgment downward for genuinely low-risk routes.

---

This audit found 17 findings (6 CRITICAL, 5 HIGH, 4 MEDIUM, 2 LOW). Nothing was changed until the user confirmed how to proceed.

## 5. Resolution

The user chose: **"Fix everything, in severity order."** 16 of 17 findings were fixed in Phase 3 — see the project's own `README.md` root ("Resultados" → Project 3) for the before/after structure, the checklist, and live validation logs. Two items from section 4 were deliberately left as-is per the "needs a decision" note: `NotificationService` remains unwired (only its hardcoded credential was fixed), and only `DELETE /tasks/<id>` was protected with auth among the task-mutating routes, matching the exact C6 scope confirmed above (not `POST`/`PUT /tasks`).

**Correction:** [C6] was originally reported as fully resolved. That was wrong. The C6 recommendation for `PUT /users/<id>` had two actions — (1) require authentication, (2) check the caller is admin before allowing the `role` field to change. Only action (1) was applied (`@login_required` on the route); the `admin_required` decorator that Phase 3 added in `utils/auth.py` was never actually called from `update_user`. Net effect: any authenticated user could still send `{"role": "admin"}` to `PUT /users/<own id>` and self-promote. Correct status for that sub-finding at the time was **PARTIALLY FIXED**, not FIXED. See section 6 for the actual fix and verification. This gap is also why `references/refactoring-playbook.md` now has pattern #21 (field-level authorization) and `SKILL.md` Phase 3 now requires checking every action of a composite recommendation before writing "FIXED".

## 6. Re-audit — [C6] `PUT /users/<id>` role field (post-correction)

- **File:** `routes/user_routes.py:26-32` (route), `services/user_service.py:93-132` (`update_user`)
- **Fix applied:** the route now rejects a `role` change from a non-admin caller before calling the service layer:
  ```python
  @user_bp.route('/users/<int:user_id>', methods=['PUT'])
  @login_required
  def update_user(user_id):
      data = request.get_json(silent=True)
      if data and 'role' in data and not g.current_user.is_admin():
          return jsonify({'error': 'Permissão de administrador necessária para alterar role'}), 403
      result = user_service.update_user(user_id, data)
      return jsonify(result), 200
  ```
- **Verified live** (app run with seed data — `joao@email.com` is `admin`, `maria@email.com` is `user`):
  ```
  $ curl -X PUT http://127.0.0.1:5000/users/2 -H "Authorization: Bearer <maria_token>" -d '{"role":"admin"}'
  {"error":"Permissão de administrador necessária para alterar role"}   # HTTP 403 — self-promotion blocked

  $ curl -X PUT http://127.0.0.1:5000/users/2 -H "Authorization: Bearer <joao_admin_token>" -d '{"role":"manager"}'
  {"active":true,...,"role":"manager"}   # HTTP 200 — admin can still change another user's role

  $ curl -X PUT http://127.0.0.1:5000/users/2 -H "Authorization: Bearer <maria_token>" -d '{"name":"Maria S. Santos"}'
  {"active":true,...,"name":"Maria S. Santos"}   # HTTP 200 — non-sensitive self-update still works
  ```
- **Status: FIXED** — both actions of the original C6 recommendation for this route are now applied: authentication (Phase 3, unchanged) and an admin check specifically gating the `role` field (this correction).
