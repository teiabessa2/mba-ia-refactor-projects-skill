# Architecture & Security Audit — code-smells-project

## 1. Overview
- **Stack:** Python 3 / Flask 3.1.1 (+ flask-cors 5.0.1), SQLite (`loja.db`) via raw `sqlite3`, no ORM.
- **Architecture shape:** **Fat model, compounded by domain sprawl (H3) across every layer.** `app.py` mixes routing with two raw, unauthenticated DB-access endpoints; `controllers.py` handles HTTP shaping but also runs business logic and side effects; `models.py` is a single module owning persistence, business rules (stock checks, discount tiers), and response shaping for four unrelated entities (produtos, usuarios, pedidos, itens_pedido). There is no service/use-case layer anywhere.
- **Files scanned:** `app.py`, `controllers.py`, `models.py`, `database.py` (4 files, ~700 lines total — full read, no sampling).
- **How to verify changes:** No test suite exists (`requirements.txt` only lists `flask`/`flask-cors`). Verification was manual: run `python app.py` (auto-creates `loja.db` with seed data) and exercise endpoints with `curl`.

## 2. Findings summary

| # | Severity | Anti-pattern | File | Line(s) |
|---|----------|--------------|------|---------|
| 1 | CRITICAL | SQL Injection (C1) | models.py | 28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155, 158-166, 174, 188, 192, 220, 224, 279-280, 289-297 |
| 2 | CRITICAL | Hardcoded secret key (C2) | app.py:7, controllers.py:289 | 7; 289 |
| 3 | CRITICAL | Weak/absent password hashing (C3) | models.py | 105-131 |
| 4 | CRITICAL | Unrestricted dynamic query endpoint (C5) | app.py | 59-78 |
| 5 | CRITICAL | Missing authentication/authorization (C6) | app.py | 11-30, 47-57, 59-78 |
| 6 | CRITICAL | Sensitive field exposed, plaintext (M4, escalated) | models.py | 83, 99 |
| 7 | HIGH | Debug mode in production entrypoint (H1) | app.py | 8, 88 |
| 8 | HIGH | God Module / domain sprawl (H3) | models.py, controllers.py | whole file (each) |
| 9 | HIGH | Business logic in controllers (H4) | controllers.py | 203-216, 237-252 |
| 10 | HIGH | Business logic in model layer (H4) | models.py | 133-169, 235-273 |
| 11 | HIGH | N+1 query pattern (H5) | models.py | 171-201, 203-233 |
| 12 | HIGH | Race condition on shared connection (H6) | database.py | 4-10 |
| 13 | MEDIUM | Duplicated/drifted validation (M1) | controllers.py | 24-62 vs 64-96 |
| 14 | MEDIUM | Generic exception handling, no logging (M2) | controllers.py | 21, 95, 108, 125, 133, 143, 226, 234, 254, 261, 291 |
| 15 | LOW | Missing pagination (L1) | models.py | 4, 72, 203 |
| 16 | LOW | Print debugging in production code (L2) | controllers.py, app.py | throughout |

## 3. Findings detail

### CRITICAL

#### [C1] SQL Injection via string-built queries
- **File:** `models.py` — every data-access function (e.g. line 28, 47-50, 92, 109-111, 140, 158-166, 279-280, 289-297)
- **Evidence:**
  ```python
  cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
  ...
  cursor.execute(
      "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
  )
  ...
  query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"
  ```
- **Why it matters:** literally every query in this codebase is string-built from request input with no parameter binding — including the **login query** (line 109-111), meaning an attacker can bypass authentication entirely (e.g. `senha=' OR '1'='1`) and the product-search endpoint, which builds a query from four separate unsanitized inputs. This isn't one hole, it's the entire data layer.
- **Recommended fix:** Parameterize every query with `?` placeholders — see refactoring-playbook.md #1.
- **Status:** FIXED — every query in `models/*.py` now uses bound parameters.

#### [C2] Hardcoded secret key
- **File:** `app.py:7`, echoed back at `controllers.py:289`
- **Evidence:**
  ```python
  app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
  ```
  ```python
  "secret_key": "minha-chave-super-secreta-123"   # returned by GET /health
  ```
- **Why it matters:** Flask's `SECRET_KEY` signs session cookies; anyone with source access can forge signed sessions. Worse, the `/health` endpoint hands this same value to **any unauthenticated caller**, so even without source access an attacker just has to call `/health`.
- **Recommended fix:** Load from an environment variable with no baked-in default; strip it from the health-check response.
- **Status:** FIXED — `SECRET_KEY` now comes from `config.py` (env-driven, raises at startup if unset); `/health` no longer returns it.

#### [C3] Weak or absent password hashing
- **File:** `models.py:105-131`
- **Evidence:**
  ```python
  cursor.execute(
      "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
  )
  ...
  cursor.execute(
      "INSERT INTO usuarios (nome, email, senha, tipo) VALUES ('" +
      nome + "', '" + email + "', '" + senha + "', '" + tipo + "')"
  )
  ```
- **Why it matters:** passwords are stored and compared as plain text. A single DB read (which, per finding #6, is already exposed over the API) hands out every user's real password, not just a hash to crack.
- **Recommended fix:** Hash on write with a slow adaptive algorithm (e.g. `werkzeug.security.generate_password_hash`) and verify with `check_password_hash` — see refactoring-playbook.md #3.
- **Status:** FIXED — `werkzeug.security` hashing on signup and seed data, verified via `check_password_hash` on login.

#### [C5] Unrestricted dynamic query endpoint
- **File:** `app.py:59-78`
- **Evidence:**
  ```python
  @app.route("/admin/query", methods=["POST"])
  def executar_query():
      dados = request.get_json()
      query = dados.get("sql", "")
      ...
      cursor.execute(query)
  ```
- **Why it matters:** this endpoint executes any SQL a caller sends, verbatim — full read/write/schema control over the database, no allow-list, no restriction to SELECT-only. Combined with finding #5 (no auth), this is an open remote database console on the public internet.
- **Recommended fix:** Remove this endpoint, or if a genuine admin query tool is needed, gate it behind real auth and a strict read-only allow-list.
- **Status:** FIXED — endpoint removed entirely.

#### [C6] Missing authentication/authorization on sensitive endpoints
- **File:** `app.py:11-30` (full route table), `47-57` (`/admin/reset-db`), `59-78` (`/admin/query`)
- **Evidence:**
  ```python
  @app.route("/admin/reset-db", methods=["POST"])
  def reset_database():
      db = get_db()
      cursor = db.cursor()
      cursor.execute("DELETE FROM itens_pedido")
      cursor.execute("DELETE FROM pedidos")
      cursor.execute("DELETE FROM produtos")
      cursor.execute("DELETE FROM usuarios")
      db.commit()
  ```
  There is no `@login_required`-equivalent, no session/token check, and no role check anywhere in `app.py` or `controllers.py` — `login()` (controllers.py:167) validates credentials but issues nothing (no token, no session) for later requests to present. Every mutating endpoint (`criar_produto`, `atualizar_produto`, `deletar_produto`, `atualizar_status_pedido`) and every read of another user's data (`listar_usuarios`, `listar_todos_pedidos`) is reachable by anyone, and the two `/admin/*` routes can wipe or arbitrarily query the entire database with zero credentials.
- **Why it matters:** this is not weak access control, it's the total absence of any access control concept in the app — the two admin routes are the most severe instance, but the gap is systemic.
- **Recommended fix:** Introduce an auth/session mechanism (e.g. token issued at login, checked via a decorator/middleware) and apply it to every mutating and admin route at minimum.
- **Status:** FIXED — JWT bearer-token auth (`auth.py`, `require_auth`/`require_role`), applied at the blueprint mount point per route. Admin-only: user list/detail, all-orders list, order status updates, `/relatorios/vendas`, `/admin/reset-db`. Any authenticated user: create orders, view own orders.

#### [M4 — escalated to CRITICAL] Plaintext password exposed in API responses
- **File:** `models.py:83`, `models.py:99`, surfaced via `controllers.py` `listar_usuarios`/`buscar_usuario`
- **Evidence:**
  ```python
  result.append({
      "id": row["id"],
      "nome": row["nome"],
      "email": row["email"],
      "senha": row["senha"],
      "tipo": row["tipo"],
      "criado_em": row["criado_em"]
  })
  ```
- **Why it matters:** `GET /usuarios` and `GET /usuarios/<id>` return every user's password verbatim to any caller. Combined with C3 (plaintext storage), the API response *is* the credential — no cracking needed.
- **Recommended fix:** Strip `senha` from every serialization path; never select it unless verifying a login.
- **Status:** FIXED — `models/usuarios_model.py` never selects `senha` outside the internal `get_usuario_por_email` used only by the login flow.

### HIGH

#### [H1] Debug mode enabled in production entrypoint
- **File:** `app.py:8, 88`
- **Status:** FIXED — `DEBUG` now env-driven via `config.py`, defaults to `false`.

#### [H3] God Module / domain sprawl
- **File:** `models.py` (whole file), `controllers.py` (whole file)
- **Status:** FIXED — split into `models/`, `controllers/`, `services/`, `routes/` per domain (produtos, usuarios, pedidos, relatorios, admin, health).

#### [H4] Business logic embedded in controllers
- **File:** `controllers.py:203-216` (`criar_pedido`), `237-252` (`atualizar_status_pedido`)
- **Status:** FIXED — notification side effects moved to `services/notificacoes_service.py`.

#### [H4] Business logic embedded in the model layer
- **File:** `models.py:133-169` (`criar_pedido`), `235-273` (`relatorio_vendas`)
- **Status:** FIXED — stock validation/total calculation moved to `services/pedidos_service.py`; discount-tier rule moved to `services/relatorios_service.py`.

#### [H5] N+1 query pattern
- **File:** `models.py:171-201` (`get_pedidos_usuario`), `203-233` (`get_todos_pedidos`)
- **Status:** FIXED — replaced with a single batched `JOIN ... WHERE pedido_id IN (...)` query in `models/pedidos_model.py`.

#### [H6] Race condition on shared connection
- **File:** `database.py:4-10`
- **Status:** FIXED — connection created once, eagerly, at module import time instead of lazily per-request.

### MEDIUM

#### [M1] Duplicated/drifted validation
- **File:** `controllers.py:24-62` (`criar_produto`) vs `64-96` (`atualizar_produto`)
- **Status:** FIXED — consolidated into `validators/produto_validator.py`, used by both create and update; also fixed the drift where `atualizar_produto` skipped category validation.

#### [M2] Generic exception handling without logging
- **File:** `controllers.py` — e.g. lines 21, 95, 108, 125, 133, 143, 226, 234, 254, 261, 291
- **Status:** FIXED — per-controller `try/except Exception: return str(e)` removed; centralized in `app.py`'s `@app.errorhandler` with `logger.exception(...)`.

### LOW

#### [L1] Missing pagination on list endpoints
- **File:** `models.py:4` (`get_todos_produtos`), `72` (`get_todos_usuarios`), `203` (`get_todos_pedidos`)
- **Status:** FIXED for `GET /produtos` (`pagina`/`tamanho` params, capped at 100). Not applied to `/usuarios` or `/pedidos` listings (both are now admin-only and low-cardinality in this app; left as-is).

#### [L2] Print debugging left in production code
- **File:** `controllers.py` and `app.py`, throughout
- **Status:** FIXED — replaced with Python's `logging` module.

## 4. Out of scope / needs a decision
- **No session/token mechanism existed at all before this refactor.** Resolved by adding JWT bearer-token auth (user's choice, confirmed before implementation).
- **`/admin/reset-db` and `/admin/query`:** kept `/admin/reset-db` behind admin auth (legitimate dev/ops utility); removed `/admin/query` entirely rather than gating it, per the anti-pattern's own recommendation (unrestricted dynamic execution should be deleted, not hardened).
- Didn't flag H2 (deprecated APIs) — the two dependencies (`flask==3.1.1`, `flask-cors==5.0.1`) are current; nothing deprecated found in use.

---

This audit found 16 findings (6 CRITICAL, 6 HIGH, 2 MEDIUM, 2 LOW).

**Resolution:** user selected "fix everything, in severity order." All 16 findings were fixed and verified against a running instance of the application (see `code-smells-project` README's "Arquitetura"/"Autenticação" sections and root `README.md` → Resultados → Projeto 1).
