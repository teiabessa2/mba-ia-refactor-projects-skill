# Anti-Pattern Catalog

Every entry is defined by a **structural signal**: a pattern in what the code
*does*, independent of the language it's written in. Use the structural
signal to decide whether something is a genuine finding — the Python and
Node examples are illustrations of that same signal, not the definition of
it. If you're auditing a language that isn't shown here, look for the
underlying signal, not the literal syntax below.

Severity is about **impact if exploited or triggered**, not how ugly the
code looks. A CRITICAL finding can leak data or let an attacker take over
the system; a LOW finding is a maintainability or scale problem that won't
cause an incident today.

Table of contents:
- CRITICAL: [C1](#c1-sql-injection-via-string-built-queries) SQL Injection · [C2](#c2-hardcoded-credentials-and-secrets) Hardcoded credentials/secrets · [C3](#c3-weak-or-absent-password-hashing) Weak/absent password hashing · [C4](#c4-forged-or-unsigned-authentication-tokens) Forged/unsigned auth tokens · [C5](#c5-unrestricted-dynamic-executionquery-endpoint) Unrestricted dynamic execution endpoint · [C6](#c6-missing-authenticationauthorization-on-sensitive-endpoints) Missing auth on sensitive endpoints
- HIGH: [H1](#h1-debug-mode-enabled-in-a-production-entrypoint) Debug mode in production · [H2](#h2-deprecated-or-eol-api-usage) Deprecated/EOL APIs · [H3](#h3-god-classgod-module) God class/module · [H4](#h4-business-logic-embedded-in-controllers-or-models) Business logic in controllers/models · [H5](#h5-n1-query-pattern) N+1 queries · [H6](#h6-race-conditions-on-shared-mutable-state) Race conditions on shared state
- MEDIUM: [M1](#m1-duplicated-or-bypassed-centralized-logic) Duplicated/bypassed centralized logic · [M2](#m2-generic-exception-handling-without-logging) Generic except without logging · [M3](#m3-callback-hell) Callback hell · [M4](#m4-sensitive-fields-exposed-in-api-responsesserialization) Sensitive fields exposed in serialization
- LOW: [L1](#l1-missing-pagination-on-list-endpoints) Missing pagination · [L2](#l2-print-console-debugging-left-in-production-code) Print/console debugging left in code

---

## CRITICAL

### C1. SQL Injection via string-built queries
**Structural signal:** a query string handed to the database driver is
assembled by concatenating, interpolating, or `%`/`.format()`-substituting
values that originate from a request, function argument, or any external
input — instead of being passed as a literal string with separate bound
parameters.

The tell isn't "the word SELECT appears near a `+`" — it's that the *shape*
of the query changes based on input value rather than only its *content*
changing. If an attacker-controlled string could inject `' OR '1'='1` or a
stacked statement and change what the query does, it's this.

Python/Flask example:
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```
Node/Express example:
```javascript
db.query(`SELECT * FROM products WHERE id = ${req.params.id}`);
```

**Why it matters:** full read/write access to the database, auth bypass,
data exfiltration — the most common route to total compromise of a backend.

---

### C2. Hardcoded credentials and secrets
**Structural signal:** a literal string in source code is used as a
cryptographic secret, API key, database password, or session-signing key —
i.e. the value that should distinguish "this deployment" from "a copy of
this code an attacker holds" is instead baked into the code an attacker can
read.

Python/Flask example:
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
Node/Express example:
```javascript
const JWT_SECRET = "super-secret-key-2024";
```

**Why it matters:** anyone with source access (a leaked repo, a decompiled
build, a public GitHub mirror) gets the same trust the server has — they can
forge sessions, decrypt data, or authenticate as anyone.

---

### C3. Weak or absent password hashing
**Structural signal:** a password is stored or compared using a fast
general-purpose hash (MD5, SHA-1, single-round SHA-256) instead of a
slow, salted, adaptive password-hashing algorithm — or it isn't hashed at
all, and is stored/compared as plain text. This also covers homemade
"encryption" that is actually just reversible **encoding** (repeated
base64, XOR, ROT13, or similar) dressed up to look like protection — the
tell is that the transformation can be undone with no secret key at all,
just by reversing the same public steps.

Python/Flask example:
```python
if usuario["senha"] == senha:   # plain-text comparison
    ...
```
Node/Express example:
```javascript
const hash = crypto.createHash('md5').update(password).digest('hex');
```
Homemade "encryption" example (also C3 — this is encoding, not hashing):
```javascript
function badCrypto(password) {
  return Buffer.from(Buffer.from(password).toString('base64')).toString('base64').slice(0, 20);
}
```

**Why it matters:** a single database leak turns into every user's real
password being recovered — via direct read (plaintext) or offline
brute-force/rainbow tables (fast hashes have no meaningful cost per guess).

---

### C4. Forged or unsigned authentication tokens
**Structural signal:** a value used to authenticate subsequent requests
(a "token", "session id", or similar) is constructed by the server without
a cryptographic signature or MAC that a client can't reproduce — e.g. it's
just an encoded/concatenated copy of user data (base64 of an email, a
predictable ID, a string template), so anyone can construct a valid-looking
token for any user without ever authenticating as them.

Python/Flask example:
```python
token = base64.b64encode(f"{user_id}:{email}".encode()).decode()
```
Node/Express example:
```javascript
const token = Buffer.from(`${userId}:${Date.now()}`).toString('base64');
```

**Why it matters:** this isn't "weak" auth, it's no auth — anyone who
notices the pattern can mint a token for any account, including an admin,
without ever knowing a password.

---

### C5. Unrestricted dynamic execution/query endpoint
**Structural signal:** an endpoint or function takes a string from the
caller and executes it directly as a database query, shell command, or code
(`eval`/`exec`/dynamic query execution) with no allow-list, sandboxing, or
restriction to a fixed set of safe operations.

Python/Flask example:
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)   # arbitrary SQL, whatever the caller sends
```
Node/Express example:
```javascript
app.post('/admin/run', (req, res) => {
  eval(req.body.code);
});
```

**Why it matters:** this is a full remote-command/remote-query interface
handed to whoever can reach the endpoint — worse than C1, because there's no
injection needed, the whole query *is* the input. Even behind "admin only"
routes, this is almost never actually needed and is a critical exposure if
the auth check is missing, weak, or bypassed.

---

### C6. Missing authentication/authorization on sensitive endpoints
**Structural signal:** an endpoint or function that performs a destructive,
administrative, or otherwise sensitive operation (deleting/resetting data,
running arbitrary queries, changing another user's records, reading private
data that isn't the caller's own) executes with **no check at all** that
confirms who the caller is or what they're allowed to do — no auth
middleware/decorator on the route, no session/token check inside the
handler, no role check before the operation runs. This is distinct from C4
(a *forgeable* token) — here there may be no authentication concept applied
to the route whatsoever.

Python/Flask example:
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_database():
    cursor.execute("DELETE FROM usuarios")   # no auth check anywhere in this handler or its route registration
```
Node/Express example:
```javascript
app.delete('/api/admin/users/:id', (req, res) => {   // no auth middleware attached to this route
  db.query('DELETE FROM users WHERE id = ?', [req.params.id]);
});
```

**Why it matters:** this isn't weak access control, it's *no* access
control — anyone who finds or guesses the URL can destroy or exfiltrate
data with zero credentials. Treat CRITICAL as the default for
admin/destructive routes; use judgment downward only for a route that is
genuinely low-value and read-only.

---

## HIGH

### H1. Debug mode enabled in a production entrypoint
**Structural signal:** the application's startup configuration enables a
framework's debug/development mode unconditionally (not gated behind an
environment variable defaulting to "off"), where that mode exposes stack
traces, interactive debuggers, source code, or auto-reload to end users.

Python/Flask example:
```python
app.run(host="0.0.0.0", port=5000, debug=True)
```
Node/Express example:
```javascript
app.use(errorhandler());  // enabled unconditionally, leaks stack traces
```

**Why it matters:** stack traces and interactive debug consoles leak file
paths, environment variables, and sometimes let a visitor execute arbitrary
code directly in the browser (e.g. Werkzeug's debugger PIN bypasses).

---

### H2. Deprecated or EOL API usage
**Structural signal:** the code calls a function, module, or language
construct that the runtime/framework/library has officially marked
deprecated, scheduled for removal, or already end-of-life for the
installed version — found via deprecation warnings the runtime emits,
changelog/migration-guide entries for the pinned dependency version, or the
library's own documentation flagging the symbol. This also covers insecure
built-ins superseded for security reasons (e.g. a legacy random-number
generator being used where a cryptographically secure one is required).

Python examples: `cgi` module (removed in 3.13), `distutils`,
`datetime.utcnow()` (deprecated in 3.12), old-style `%` string formatting
mixed with SQL (a red flag combined with C1), `flask.ext.*` import style.
Node examples: callback-style `fs` APIs in a codebase that has migrated to
promises elsewhere, `new Buffer()` (deprecated in favor of
`Buffer.from`/`Buffer.alloc`), body-parser included standalone when Express
≥4.16 bundles it, `request` package (fully deprecated, unmaintained).

**Why it matters:** deprecated APIs lose security patches first, often have
known unfixed issues, and block upgrading the runtime/framework later —
technical debt that becomes a security problem on a delay.

---

### H3. God Class/Module
**Structural signal:** a single file, class, or module owns data access,
business rules, and formatting/presentation logic for multiple unrelated
domain entities (e.g. products, users, *and* orders all live in one
`models.py` or `db.js`), or a single function/handler does noticeably more
than its name implies. A useful heuristic: if you can't describe the
file's responsibility in one sentence without using "and", it's a
candidate.

**Why it matters:** every change risks unrelated regressions, the file
becomes a merge-conflict magnet, and it's impossible to test one
responsibility without dragging in all the others.

---

### H4. Business logic embedded in controllers or models
**Structural signal:** a route handler (controller) or a data-access
function (model) contains decision logic that isn't about HTTP
request/response shaping (controller) or data persistence shape (model) —
e.g. computing derived business values, orchestrating multi-step workflows,
enforcing business rules beyond basic input shape, or triggering side
effects like notifications — with no intermediate service/use-case layer.

Python/Flask example (inside a controller):
```python
def criar_pedido():
    resultado = models.criar_pedido(usuario_id, itens)
    print("ENVIANDO EMAIL: Pedido criado...")
    print("ENVIANDO SMS: ...")
    print("ENVIANDO PUSH: ...")
```

**Why it matters:** logic scattered across the HTTP and data layers can't be
reused (e.g. by a background job or CLI), can't be unit-tested without an
HTTP request or a database, and duplicates itself as soon as a second entry
point needs the same rule.

---

### H5. N+1 query pattern
**Structural signal:** a loop iterates over a collection fetched from the
database, and the loop body issues one additional query per item (to fetch
a related record, a count, or a lookup) instead of fetching all needed data
in one batched query (a `JOIN`, an `IN (...)` query, or a single aggregate
query) before or instead of the loop.

Python example:
```python
pedidos = get_todos_pedidos()
for pedido in pedidos:
    pedido["itens"] = get_itens_do_pedido(pedido["id"])  # one query per pedido
```
Node example:
```javascript
const orders = await Order.findAll();
for (const order of orders) {
  order.items = await Item.findAll({ where: { orderId: order.id } });
}
```

**Why it matters:** response time scales linearly with result-set size;
what's fast in dev with 10 rows becomes a multi-second (or timing-out)
request in production with 10,000.

---

### H6. Race conditions on shared mutable state
**Structural signal:** concurrent or asynchronous execution paths (threads,
async tasks, event-loop callbacks, worker processes) read and write the
same in-memory state (a global variable, a module-level cache, a shared
connection object, a counter) without synchronization (locks, atomic
operations, or serializing access through a single owner), where the
outcome depends on execution order.

Python example:
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:          # two requests can both see None
        db_connection = sqlite3.connect(...)   # and both create a connection
    return db_connection
```
Node example:
```javascript
let requestCount = 0;
app.use((req, res, next) => { requestCount++; next(); });  // lost updates under concurrency
```
A common Node-specific manifestation: manually counting completed async
callbacks to detect "all done" instead of using `Promise.all` — the counter
itself becomes the shared mutable state at risk, and under retries or
partial errors the completion check can fire more than once or never.
```javascript
let completed = 0;
const results = [];
items.forEach((item, i) => {
  fetchData(item, (err, data) => {
    results[i] = data;
    completed++;
    if (completed === items.length) {   // can be reached twice if a callback re-fires, or never if one drops
      res.json(results);                // symptom: res.json() called more than once, or the request hangs
    }
  });
});
```

**Why it matters:** intermittent, hard-to-reproduce bugs — corrupted
counters, double-processed payments, two connections silently overwriting
each other, or (in the fan-in case above) a response sent twice or never.
These fail in production under load and rarely in local testing.

---

## MEDIUM

### M1. Duplicated or bypassed centralized logic
**Structural signal:** the same field-level checks (required fields, type
checks, range/length checks, allowed-values lists) **or the same business
rule/calculation** are re-implemented independently at multiple call sites
instead of being defined once and reused. This includes the more insidious
variant where a shared function or utility **already exists** in the
codebase for exactly this purpose, but call sites silently reimplement the
logic inline instead of calling it — a sign the abstraction was built but
never adopted. Spot the validation variant when two endpoints for the same
entity (create/update) have near-identical but independently-maintained
checks; spot the bypassed-utility variant by finding a well-named
function/method that's never called from the places that need exactly what
it does.

Python example (bypassed utility, not just validation):
```python
# models/task.py — the canonical rule
def is_overdue(self):
    return self.due_date < datetime.utcnow() and self.status != "done"

# routes/report_routes.py — reimplemented instead of calling task.is_overdue(),
# and note it's already drifted: this version adds a "cancelled" check the
# original method doesn't have
if task.due_date < datetime.utcnow():
    if task.status != "done":
        if task.status != "cancelled":
            overdue = True
```

**Why it matters:** the checks or the rule drift apart over time (one copy
gets updated, the others don't), producing inconsistent behavior between
call sites for what should be a single source of truth — a correctness and,
for validation specifically, a security gap, not just duplication. When a
utility already exists and is bypassed, it also means the team already
identified the right fix and it isn't reaching production.

---

### M2. Generic exception handling without logging
**Structural signal:** a broad catch-all (`except Exception`, bare
`except:`, `catch (e)`) swallows the error — converting it to a generic
response or silently continuing — without recording the original
exception (type, message, stack trace) anywhere a developer could later
find it. Returning `str(e)` directly to the HTTP caller counts as *worse*
than silence: it both hides root cause from operators and leaks internals
to users.

**Why it matters:** when something breaks in production, there's no trail
to diagnose it — the specific failure is thrown away at the exact moment
it would have been most useful.

---

### M3. Callback hell
**Structural signal:** asynchronous operations are chained by nesting each
next step inside the callback of the previous one, several levels deep,
instead of using a flat sequential construct (`async`/`await`, promise
chaining, coroutines) — recognizable by indentation that grows with every
additional async step and error handling repeated at every nesting level.

Node example:
```javascript
getUser(id, (err, user) => {
  getOrders(user.id, (err, orders) => {
    getItems(orders[0].id, (err, items) => {
      calculateTotal(items, (err, total) => { /* ... */ });
    });
  });
});
```

**Why it matters:** error handling is easy to miss at any one level,
control flow is hard to follow, and adding one more step means one more
level of nesting — the code gets harder to change exactly when it needs to
change.

---

### M4. Sensitive fields exposed in API responses/serialization
**Structural signal:** a function that turns a domain object into an HTTP
response (a `to_dict()`/`toJSON()` method, a manual dict/object literal, a
model instance passed straight to a JSON serializer) includes a field that
should never leave the server — a password, a password hash, a full
token/secret, a payment credential — with no explicit step stripping it out
before the object reaches the response.

Python/Flask example:
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password_hash}   # leaves the hash in every response
```
Node/Express example:
```javascript
res.json(user);   // user is the raw DB row/model instance, including passwordHash
```

**Why it matters:** even a properly-hashed password should never reach a
client — it hands out a value whose only purpose is offline verification,
turning every response into a cracking opportunity. Treat this as MEDIUM on
its own; it escalates to CRITICAL when the exposed value is itself
unhashed or weakly hashed (see C3), since then the response *is* the
credential, not just material for cracking it later.

---

## LOW

### L1. Missing pagination on list endpoints
**Structural signal:** an endpoint or function that returns "all" rows of a
table/collection has no limit/offset, page/size, or cursor parameters —
it fetches and returns the entire table every time regardless of size.

**Why it matters:** response size and query cost grow unbounded with the
data — fine at 10 rows, a slow or failing endpoint at 1,000,000.

---

### L2. Print/console debugging left in production code
**Structural signal:** `print()`/`console.log()` (or equivalent) calls are
used in place of a structured logger for operational messages (request
lifecycle, errors, state changes) — recognizable because there's no log
level, no way to filter by severity or module, and no way to redirect
output without editing code.

**Why it matters:** unfiltered ad-hoc output makes production logs noisy
and hard to search, and there's no way to turn down verbosity without a
code change and redeploy.
