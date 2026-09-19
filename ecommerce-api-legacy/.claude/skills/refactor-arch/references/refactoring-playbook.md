# Refactoring Playbook (Phase 3)

One transformation per anti-pattern in `antipattern-catalog.md`. Adapt the
pattern to the project's existing naming and idioms — these are before/after
*examples*, not snippets to paste verbatim. Apply one at a time and verify
after each (see SKILL.md Phase 3, step 3-4).

This file is long — jump straight to the entry for the finding you're fixing
instead of reading start to finish; the table of contents below maps each
anti-pattern ID to its transformation.

Table of contents:
- CRITICAL: [#1](#1-parameterize-sql-queries-fixes-c1) Parameterize SQL (C1) · [#2](#2-externalize-secrets-to-environmentconfig-fixes-c2) Externalize secrets (C2) · [#3](#3-replace-weakplaintext-password-handling-with-adaptive-hashing-fixes-c3) Adaptive password hashing (C3) · [#4](#4-replace-forged-tokens-with-signed-verifiable-tokens-fixes-c4) Signed tokens (C4) · [#5](#5-remove-or-restrict-dynamic-execution-endpoints-fixes-c5) Remove dynamic execution (C5) · [#17](#17-add-authenticationauthorization-checks-to-sensitive-endpoints-fixes-c6) Add auth checks (C6)
- HIGH: [#6](#6-disable-debug-mode-via-environment-driven-config-fixes-h1) Debug mode via config (H1) · [#7](#7-replace-deprecated-apis-with-their-maintained-equivalents-fixes-h2) Replace deprecated APIs (H2) · [#8](#8-split-a-god-classmodule-by-domain-fixes-h3) Split God Class/Module (H3) · [#9](#9-extract-business-logic-into-a-service-layer-fixes-h4) Extract service layer (H4) · [#10](#10-batch-queries-to-eliminate-n1-fixes-h5) Batch queries / fix N+1 (H5) · [#11](#11-serialize-access-to-shared-mutable-state-fixes-h6) Serialize shared state (H6)
- MEDIUM: [#12](#12-centralize-validation-or-business-rules-into-one-reusable-definition-fixes-m1) Centralize validation/logic (M1) · [#13](#13-catch-specific-exceptions-and-log-before-responding-fixes-m2) Log specific exceptions (M2) · [#14](#14-flatten-callback-hell-with-asyncawait-fixes-m3) Flatten callback hell (M3) · [#18](#18-strip-sensitive-fields-before-serialization-fixes-m4) Strip sensitive fields (M4)
- LOW: [#15](#15-add-pagination-to-list-endpoints-fixes-l1) Add pagination (L1) · [#16](#16-replace-ad-hoc-prints-with-structured-logging-fixes-l2) Structured logging (L2)
- ARCHITECTURE (complete the MVC split, not tied to one severity): [#19](#19-extract-route-registration-into-routerblueprint-modules-completes-h3--mvc-layout) Router/Blueprint extraction · [#20](#20-centralize-error-handling-in-one-framework-level-handler-extends-m2) Centralized error handler
- CRITICAL (companion to C6, applies even when route-level auth exists): [#21](#21-add-field-level-authorization-for-sensitive-attributes-in-partial-updates) Field-level authorization for sensitive attributes

---

## 1. Parameterize SQL queries (fixes C1)

Never build a query string from untrusted input. Pass values as bound
parameters and let the driver handle escaping — this also happens to make
the code shorter.

**Before:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```
**After:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```
Node/Express equivalent — before:
```javascript
db.query(`SELECT * FROM products WHERE id = ${req.params.id}`);
```
after:
```javascript
db.query('SELECT * FROM products WHERE id = ?', [req.params.id]);
```
If an ORM is available, prefer its query builder (`Model.findByPk(id)`)
over raw SQL entirely — it parameterizes by construction.

---

## 2. Externalize secrets to environment/config (fixes C2)

Move every credential/key out of source and into environment variables (or
a secrets manager for production), loaded through a single config module —
never scattered `os.environ.get()` calls at the point of use, so there's
one place that knows every required variable.

**Before:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
**After:**
```python
# config.py
import os
SECRET_KEY = os.environ["SECRET_KEY"]   # raises loudly if unset — no silent fallback to a weak default

# app.py
app.config["SECRET_KEY"] = config.SECRET_KEY
```
Node/Express equivalent — before:
```javascript
const JWT_SECRET = "super-secret-key-2024";
```
after:
```javascript
// config/index.js
require('dotenv').config();
module.exports = {
  jwtSecret: process.env.JWT_SECRET,   // throws downstream if consumed while undefined — add a startup check if you want it to fail loudly
};

// app.js
const config = require('./config');
```
Commit a `.env.example` with the variable names (not values) and add real
`.env` files to `.gitignore`. If a secret was ever committed, rotating it
is necessary — removing it from new commits doesn't remove it from git
history.

Before adding a new env-loading mechanism, check whether the project
already depends on a dotenv-style library (`python-dotenv` in
`requirements.txt`, `dotenv` in `package.json`) that simply isn't wired up
yet — the fix is sometimes one `load_dotenv()` call away, not a new
dependency.

---

## 3. Replace weak/plaintext password handling with adaptive hashing (fixes C3)

Hash on write with a slow, salted, adaptive algorithm (bcrypt, scrypt, or
argon2); verify on read with that library's compare function — never
compare hashes or passwords with `==`.

**Before:**
```python
if usuario["senha"] == senha:
    ...
```
**After:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

# on signup
senha_hash = generate_password_hash(senha)   # store senha_hash, never the raw password

# on login
if check_password_hash(usuario["senha_hash"], senha):
    ...
```
Node/Express equivalent, using `bcrypt`:
```javascript
const hash = await bcrypt.hash(password, 12);      // signup
const ok = await bcrypt.compare(password, user.passwordHash);  // login
```
Existing plaintext/weakly-hashed passwords in the database can't be
migrated in place (you can't un-hash MD5 or recover plaintext safely) —
flag this to the user as needing a forced password reset for existing
users, it's a decision outside the code change itself.

---

## 4. Replace forged tokens with signed, verifiable tokens (fixes C4)

Use a vetted library to issue a token that's cryptographically signed
(HMAC or asymmetric) with a secret the client never sees, and verify the
signature — not just decode the payload — on every request that relies on
it. Include an expiry.

**Before:**
```python
token = base64.b64encode(f"{user_id}:{email}".encode()).decode()
```
**After:**
```python
import jwt, datetime

token = jwt.encode(
    {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)},
    config.SECRET_KEY,
    algorithm="HS256",
)

# verifying a request:
try:
    payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
except jwt.InvalidTokenError:
    return jsonify({"erro": "Token inválido"}), 401
```
The critical part isn't the library choice, it's that verification checks
a signature the caller cannot produce without the secret — decoding a
base64 payload is not verification.

---

## 5. Remove or restrict dynamic execution endpoints (fixes C5)

Delete endpoints that execute arbitrary caller-supplied SQL/code. If the
underlying need is legitimate (e.g. an internal reporting tool), replace it
with a fixed set of parameterized, purpose-built queries/operations behind
real authorization — never a pass-through to `execute()`/`eval()`.

**Before:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)
```
**After:** delete the endpoint; expose only specific, parameterized
reporting endpoints instead:
```python
@app.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    return jsonify(relatorios_service.gerar_relatorio_vendas())
```
If ad-hoc querying is genuinely required (e.g. for internal ops), put it
behind a separate authenticated admin tool with query allow-listing and
audit logging — not a public application endpoint.

---

## 6. Disable debug mode via environment-driven config (fixes H1)

Debug/verbose-error mode should be controlled by an environment variable
that defaults to **off**, never hardcoded on.

**Before:**
```python
app.run(host="0.0.0.0", port=5000, debug=True)
```
**After:**
```python
# config.py
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

# app.py
app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
```
Also remove debug-only information from any response payload (e.g. a
`health` endpoint that returns the secret key or `debug: true` — that's a
C2/H1 combination, fix both).

---

## 7. Replace deprecated APIs with their maintained equivalents (fixes H2)

Check the runtime/framework's own deprecation warnings and migration guide
for the pinned version, then swap the call for its documented replacement —
don't just suppress the warning.

**Before (Python):**
```python
timestamp = datetime.datetime.utcnow()
```
**After:**
```python
timestamp = datetime.datetime.now(datetime.timezone.utc)
```
**Before (Node):**
```javascript
const buf = new Buffer(data);
```
**After:**
```javascript
const buf = Buffer.from(data);
```
Run the project's test suite (or the app itself, if none exists) after
each swap — deprecated-but-not-yet-removed APIs sometimes have subtly
different replacement semantics (e.g. timezone-aware vs. naive datetimes),
not just a renamed call.

---

## 8. Split a God Class/Module by domain (fixes H3)

Break one file covering multiple unrelated entities into one file per
entity, each exposing only the operations for that entity. Do this before
introducing the controller/service/model split (playbook #9) if both apply
— splitting by domain first makes the layering split mechanical.

**Before:** `models.py` containing `get_todos_produtos`, `criar_usuario`,
`login_usuario`, `criar_pedido`, `relatorio_vendas`, etc., all in one file.

**After:**
```
models/produtos_model.py   # get_todos_produtos, get_produto_por_id, criar_produto, ...
models/usuarios_model.py   # get_todos_usuarios, criar_usuario, login_usuario, ...
models/pedidos_model.py    # criar_pedido, get_pedidos_usuario, relatorio_vendas, ...
```
Update imports at call sites; this step is mechanical (moving functions,
fixing imports) and low-risk, which makes it a good first step in a larger
refactor — it doesn't change behavior, only location.

---

## 9. Extract business logic into a service layer (fixes H4)

Introduce a service function between the controller and the model. The
controller keeps only request parsing and response shaping; the service
owns the workflow and any side effects.

**Before (in a controller):**
```python
def criar_pedido():
    dados = request.get_json()
    resultado = models.criar_pedido(dados["usuario_id"], dados["itens"])
    print("ENVIANDO EMAIL: Pedido criado...")
    print("ENVIANDO SMS: ...")
    return jsonify({"dados": resultado}), 201
```
**After:**
```python
# services/pedidos_service.py
def criar_pedido(usuario_id, itens):
    resultado = pedidos_model.criar_pedido(usuario_id, itens)
    notificacoes_service.notificar_novo_pedido(resultado["pedido_id"], usuario_id)
    return resultado

# controllers/pedidos_controller.py
def criar_pedido():
    dados = request.get_json()
    resultado = pedidos_service.criar_pedido(dados["usuario_id"], dados["itens"])
    return jsonify({"dados": resultado}), 201
```
Now `pedidos_service.criar_pedido` is callable from a background job or a
test with no HTTP request involved — that's the concrete payoff, not just
"cleaner code."

---

## 10. Batch queries to eliminate N+1 (fixes H5)

Replace a per-item query inside a loop with a single batched fetch (an
`IN (...)` query, a `JOIN`, or an ORM eager-load) before or instead of the
loop.

**Before:**
```python
pedidos = get_todos_pedidos()
for pedido in pedidos:
    pedido["itens"] = get_itens_do_pedido(pedido["id"])   # one query per pedido
```
**After:**
```python
pedidos = get_todos_pedidos()
pedido_ids = [p["id"] for p in pedidos]
itens_por_pedido = get_itens_para_pedidos(pedido_ids)   # single query with WHERE pedido_id IN (...)
for pedido in pedidos:
    pedido["itens"] = itens_por_pedido.get(pedido["id"], [])
```
Node/ORM equivalent: replace a per-row `await Model.find(...)` inside a
`for`/`.map()` with `Model.findAll({ where: { id: idList }, include: [...] })`
or the ORM's eager-loading option.

---

## 11. Serialize access to shared mutable state (fixes H6)

Either make the shared resource's initialization atomic (a lock around
first-use creation), or avoid module-level mutable shared state entirely by
creating the resource once at startup instead of lazily on first request.

**Before:**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(db_path)
    return db_connection
```
**After (eager init — simplest fix when startup cost is acceptable):**
```python
# created once, at import/startup time, not lazily per-request
db_connection = sqlite3.connect(db_path, check_same_thread=False)
def get_db():
    return db_connection
```
If lazy initialization is required, guard it with a lock instead:
```python
import threading
_lock = threading.Lock()
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        with _lock:
            if db_connection is None:   # re-check inside the lock
                db_connection = sqlite3.connect(db_path)
    return db_connection
```
For counters/aggregates under concurrency, use an atomic increment
(a database `UPDATE ... SET count = count + 1`, or a language-level atomic
primitive) instead of read-modify-write on a plain variable.

For the Node fan-in variant (a manual counter tracking how many parallel
callbacks have completed), replace the counter with `Promise.all` so
completion is tracked by the runtime instead of hand-rolled state:

**Before:**
```javascript
let completed = 0;
const results = [];
items.forEach((item, i) => {
  fetchData(item, (err, data) => {
    results[i] = data;
    completed++;
    if (completed === items.length) {
      res.json(results);   // can fire twice, or never, under retries/errors
    }
  });
});
```
**After:**
```javascript
const fetchDataAsync = util.promisify(fetchData);
const results = await Promise.all(items.map(item => fetchDataAsync(item)));
res.json(results);   // resolves exactly once, rejects on the first error
```

---

## 12. Centralize validation or business rules into one reusable definition (fixes M1)

Define each field's rules — or each business rule/calculation — once (a
schema, a DTO class, a shared validation function, or a model method) and
reuse it across every call site that needs it, instead of re-writing or
reimplementing the logic per endpoint. If a shared utility already exists
and call sites bypass it, the fix is to call it, not to write another copy.

**Before:** near-identical `if "nome" not in dados: ...` blocks repeated in
both `criar_produto` and `atualizar_produto`.

**After:**
```python
# validators/produto_validator.py
def validar_produto(dados, parcial=False):
    erros = []
    if not parcial and "nome" not in dados:
        erros.append("Nome é obrigatório")
    if "nome" in dados and not (2 <= len(dados["nome"]) <= 200):
        erros.append("Nome deve ter entre 2 e 200 caracteres")
    # ... remaining rules, defined once
    return erros

# both criar_produto and atualizar_produto controllers call validar_produto(dados)
```
A schema library (`pydantic`, `marshmallow`, `zod`, `joi`) gets you this for
free with less hand-written code — prefer one if the project already has a
dependency on one, or if introducing one is in scope.

The bypassed-utility variant is a call-site fix, not a new abstraction —
the canonical logic already exists, callers just need to use it:

**Before:** a model already defines the rule, but routes reimplement it by hand:
```python
# models/task.py — canonical rule, already exists
def is_overdue(self):
    return self.due_date < datetime.utcnow() and self.status != "done"

# routes/report_routes.py — reimplemented inline instead of calling it
if task.due_date < datetime.utcnow():
    if task.status != "done":
        overdue = True
```
**After:**
```python
overdue = task.is_overdue()
```
When you find this pattern, check every other call site for the same
reimplementation — if one route bypassed the canonical method, others
likely did too.

---

## 13. Catch specific exceptions and log before responding (fixes M2)

Catch the narrowest exception type you can act on, log the full exception
(not just its message) with context, and return a generic message to the
caller — never `str(e)` directly to an HTTP response.

**Before:**
```python
except Exception as e:
    return jsonify({"erro": str(e)}), 500
```
**After:**
```python
import logging
logger = logging.getLogger(__name__)

except sqlite3.IntegrityError as e:
    logger.warning("Integrity error creating produto: %s", e)
    return jsonify({"erro": "Produto inválido ou duplicado"}), 400
except Exception as e:
    logger.exception("Unexpected error creating produto")   # logs full traceback
    return jsonify({"erro": "Erro interno"}), 500
```
The generic `except Exception` branch can stay as a last-resort safety net —
the fix is adding the log and removing internal detail from the response,
plus catching specific exceptions above it where you can act differently.

---

## 14. Flatten callback hell with async/await (fixes M3)

Convert nested callbacks into a flat sequence using the language's native
async construct, with error handling in one place.

**Before:**
```javascript
getUser(id, (err, user) => {
  if (err) return handleError(err);
  getOrders(user.id, (err, orders) => {
    if (err) return handleError(err);
    getItems(orders[0].id, (err, items) => {
      if (err) return handleError(err);
      calculateTotal(items, (err, total) => {
        if (err) return handleError(err);
        res.json({ total });
      });
    });
  });
});
```
**After:**
```javascript
try {
  const user = await getUser(id);
  const orders = await getOrders(user.id);
  const items = await getItems(orders[0].id);
  const total = await calculateTotal(items);
  res.json({ total });
} catch (err) {
  handleError(err);
}
```
This requires the underlying functions to return promises — if they're
callback-based, wrap them (`util.promisify` in Node) rather than rewriting
every low-level function.

---

## 15. Add pagination to list endpoints (fixes L1)

Accept a page/size (or cursor) parameter, apply it in the query itself
(not by fetching everything and slicing in memory), and return pagination
metadata alongside the results.

**Before:**
```python
def get_todos_produtos():
    cursor.execute("SELECT * FROM produtos")
    return cursor.fetchall()
```
**After:**
```python
def get_produtos_paginado(pagina=1, tamanho=20):
    offset = (pagina - 1) * tamanho
    cursor.execute("SELECT * FROM produtos LIMIT ? OFFSET ?", (tamanho, offset))
    itens = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    total = cursor.fetchone()[0]
    return {"itens": itens, "pagina": pagina, "tamanho": tamanho, "total": total}
```
Cap `tamanho` at a sane maximum server-side (e.g. 100) so a caller can't
request the entire table anyway by passing a huge page size.

---

## 16. Replace ad-hoc prints with structured logging (fixes L2)

Use the language/framework's logging facility with levels, and configure
output/verbosity at the application boundary instead of at each call site.

**Before:**
```python
print("ERRO ao criar produto: " + str(e))
```
**After:**
```python
import logging
logger = logging.getLogger(__name__)
logger.error("Erro ao criar produto: %s", e)
```
Node equivalent — replace `console.log`/`console.error` with a logger
(`pino`, `winston`) configured once and imported everywhere, so log level
and output destination are controlled centrally.

---

## 17. Add authentication/authorization checks to sensitive endpoints (fixes C6)

Attach a real auth check — middleware, decorator, or an explicit check at
the top of the handler — that verifies identity and permission *before*
any destructive or sensitive work happens. This is different from playbook
#4 (fixing a forgeable token): here the goal is making sure a check exists
at all.

**Before:**
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    cursor.execute("DELETE FROM usuarios")
```
**After:**
```python
@app.route("/admin/reset-db", methods=["POST"])
@require_role("admin")   # verifies a valid, signed session/token and role before the handler runs
def reset_database():
    cursor.execute("DELETE FROM usuarios")
```
Node/Express equivalent:
```javascript
router.delete('/api/admin/users/:id', requireAdmin, usersController.remove);
```
If the project has no auth system at all yet, that's a decision for the
user, not something to pick unilaterally (session-based vs. JWT vs. API
key changes the shape of every other endpoint) — surface it in the audit's
"needs a decision" section rather than choosing one during the refactor.

---

## 18. Strip sensitive fields before serialization (fixes M4)

Build the response payload from an explicit allowlist of fields to
include, rather than passing a raw model/row through — a denylist
("exclude these fields") silently leaks any new sensitive field added
later that nobody remembered to exclude.

**Before:**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password_hash}
```
**After:**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email}   # password_hash never leaves the model
```
Node/Express equivalent:
```javascript
function toPublicUser(user) {
  const { id, email, name } = user;   // passwordHash intentionally omitted
  return { id, email, name };
}
res.json(toPublicUser(user));
```
Apply this to every serialization path for the entity, including ones that
look incidental — a login response, a "list all users" endpoint, and a
"get one user" endpoint often call different code and can each leak the
field independently even after one is fixed.

---

## 19. Extract route registration into Router/Blueprint modules (completes H3 / MVC layout)

Once controllers are split by domain (playbook #8), split routing the same
way — one router/blueprint per domain, mounted from the entrypoint. This
isn't a fix for a single catalog ID on its own; it's what makes the H3
domain split and the H4 service extraction actually stick, instead of
leaving every route still registered in one long list in the entrypoint.

**Before (routes registered inline in the entrypoint):**
```python
# app.py
app.add_url_rule("/produtos", "listar_produtos", produtos_controller.listar_produtos, methods=["GET"])
app.add_url_rule("/usuarios", "listar_usuarios", usuarios_controller.listar_usuarios, methods=["GET"])
# ...12 more lines mixing every domain together
```
**After:**
```python
# routes/produtos_routes.py
from flask import Blueprint
from controllers import produtos_controller

produtos_bp = Blueprint("produtos", __name__)
produtos_bp.add_url_rule("/produtos", "listar_produtos", produtos_controller.listar_produtos, methods=["GET"])

# app.py
from routes.produtos_routes import produtos_bp
app.register_blueprint(produtos_bp)
```
Node/Express equivalent — before:
```javascript
// app.js — every route for every domain registered directly on the app
app.get('/products', productsController.list);
app.get('/users', usersController.list);
```
after:
```javascript
// routes/products.routes.js
const router = require('express').Router();
const productsController = require('../controllers/products.controller');
router.get('/products', productsController.list);
module.exports = router;

// app.js
app.use(require('./routes/products.routes'));
```
The payoff shows up the next time an endpoint needs auth middleware: with
routing centralized per domain, protecting a whole domain (or one route in
it) is a one-line change at the mount point, not a change scattered across
every handler.

---

## 20. Centralize error handling in one framework-level handler (extends M2)

Playbook #13 fixes each `except Exception`/`catch` to log properly instead
of leaking `str(e)`. Once every controller does that *consistently*, the
duplication itself becomes the next problem — the same three lines are
copy-pasted into every function. Delete the repetition and let the
framework's centralized error path own it instead.

**Before (repeated in every controller function):**
```python
def criar_produto():
    try:
        ...
    except Exception as e:
        logger.exception("Erro ao criar produto")
        return jsonify({"erro": "Erro interno"}), 500
```
**After (no try/except in the controller at all):**
```python
def criar_produto():
    ...  # an uncaught exception here now bubbles up automatically

# app.py
from werkzeug.exceptions import HTTPException

@app.errorhandler(HTTPException)
def handle_http_error(e):
    return jsonify({"erro": e.description}), e.code   # keep Flask's own 404/400/405 as JSON, not HTML

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    logger.exception("Unhandled error")
    return jsonify({"erro": "Erro interno"}), 500
```
Node/Express equivalent — before:
```javascript
async function createProduct(req, res) {
  try {
    // ...
  } catch (e) {
    console.error(e);
    res.status(500).json({ erro: e.message });   // also leaks internals — see catalog M2
  }
}
```
after:
```javascript
async function createProduct(req, res, next) {
  try {
    // ...
  } catch (e) {
    next(e);   // hand off to the centralized handler instead of formatting a response here
  }
}

// registered last, after every app.use(routerX) call — Express identifies
// error middleware by this exact 4-argument signature
app.use((err, req, res, next) => {
  logger.error(err.stack);
  const status = err.statusCode || 500;
  res.status(status).json({ erro: status === 500 ? 'Erro interno' : err.message });
});
```
Keep any `try/except`/`catch` that reacts *differently* to a specific
exception type (e.g. a duplicate-key error returning 409 instead of 500) —
centralizing removes the repeated generic catch-all, not deliberate,
type-specific error handling.

---

## 21. Add field-level authorization for sensitive attributes in partial updates

When an endpoint accepts a partial update (PATCH/PUT) and the payload can
touch one or more sensitive fields — `role`, `permissions`, `is_admin`,
`balance`, a payment/subscription status, etc. — route-level checks like
"the caller is authenticated" or even "the caller owns this resource" are
**not sufficient**. Those checks answer "can this caller touch this
resource at all", not "can this caller set this specific field". Add an
explicit check for the sensitive field(s), applied before the change is
persisted, that runs regardless of whatever route-level auth is already in
place. This is a companion to playbook #17/catalog C6: #17 fixes a route
with *no* auth check at all, this pattern fixes a route that has auth but
still lets an authorized caller escalate privilege through an
under-guarded field.

A decorator like `admin_required` is usually built for gating an entire
route, so it often doesn't fit cleanly onto a handler that must allow
*some* fields through for any authenticated/owning caller and only gate
one or two fields. Prefer an inline check next to (or inside) the update
logic over trying to force the whole route behind an all-or-nothing
decorator.

**Before (Flask):**
```python
@app.route("/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    if "name" in data:
        user.name = data["name"]
    if "role" in data:
        user.role = data["role"]   # any authenticated caller can set this
    db.session.commit()
    return jsonify(user.to_dict())
```
**After (Flask):**
```python
@app.route("/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    data = request.get_json()
    if "role" in data and not g.current_user.is_admin():
        return jsonify({"error": "Permissão de administrador necessária"}), 403
    user = User.query.get_or_404(user_id)
    if "name" in data:
        user.name = data["name"]
    if "role" in data:
        user.role = data["role"]
    db.session.commit()
    return jsonify(user.to_dict())
```

**Before (Express):**
```javascript
router.put('/users/:id', requireAuth, async (req, res) => {
  const user = await User.findByPk(req.params.id);
  if (req.body.name !== undefined) user.name = req.body.name;
  if (req.body.role !== undefined) user.role = req.body.role;   // any authenticated caller can set this
  await user.save();
  res.json(user);
});
```
**After (Express):**
```javascript
router.put('/users/:id', requireAuth, async (req, res) => {
  if (req.body.role !== undefined && !req.user.isAdmin()) {
    return res.status(403).json({ error: 'Admin role required' });
  }
  const user = await User.findByPk(req.params.id);
  if (req.body.name !== undefined) user.name = req.body.name;
  if (req.body.role !== undefined) user.role = req.body.role;
  await user.save();
  res.json(user);
});
```

This applies to any composite update endpoint with a sensitive field, not
just `role` — audit each field the payload accepts, not just the route as
a whole, and check ownership-based endpoints too: "the caller owns this
record" does not imply "the caller may set every field on this record".
