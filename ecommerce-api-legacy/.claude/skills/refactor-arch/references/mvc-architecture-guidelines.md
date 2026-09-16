# MVC Architecture Guidelines (Phase 3 target)

MVC on a backend API (no server-rendered views in most cases) means three
layers with a strict one-directional dependency: **routes/controllers**
depend on **services**, **services** depend on **models**. Nothing depends
back upward. If you find yourself importing a controller from a model,
that's the boundary breaking.

## The three layers

**Controllers** (sometimes called "routes" or "handlers")
- Parse and validate the *shape* of the request (required fields present,
  correct types, well-formed JSON) — not business rules.
- Call exactly one service function to do the actual work.
- Translate the service's result (or exception) into an HTTP response
  (status code, JSON body).
- Should contain **no** direct database access and **no** business
  decisions (pricing rules, workflow steps, what counts as valid stock,
  what triggers a notification).

**Services** (sometimes called "use cases" or "business logic layer")
- Own the business rules: what "valid" means beyond basic shape, what
  happens in what order, what triggers a side effect (sending a
  notification, updating related records).
- Orchestrate one or more model calls to fulfill a use case.
- Have no knowledge of HTTP — a service function should be callable from a
  CLI script, a background job, or a test with no request/response objects
  involved.
- This is the layer that existed as an afterthought in most of the
  anti-patterns in the catalog (H4) — introducing it is usually the single
  biggest structural change in a refactor.

**Models** (sometimes called "repositories" when the split is more formal)
- Own data access and the shape data takes in storage.
- Every query touching the database lives here — parameterized, always
  (see catalog C1 and playbook #1).
- No business rules, no response formatting for HTTP, no side effects
  like sending notifications.

## Suggested layout — Python/Flask

```
project/
├── app.py                  # app factory / entrypoint only: create app, register blueprints
├── config.py                # environment-driven configuration (see playbook #2)
├── controllers/
│   ├── produtos_controller.py
│   ├── usuarios_controller.py
│   └── pedidos_controller.py
├── services/
│   ├── produtos_service.py
│   ├── usuarios_service.py
│   └── pedidos_service.py
├── models/
│   ├── produtos_model.py
│   ├── usuarios_model.py
│   └── pedidos_model.py
├── database.py               # connection/session management only
└── tests/
```

If the project uses Flask blueprints, one blueprint per domain (products,
users, orders) mapping 1:1 to a controller module keeps routing and
controller code co-located and easy to find.

## Suggested layout — Node.js/Express

```
project/
├── app.js / server.js         # entrypoint: create app, mount routers
├── config/
│   └── index.js                # environment-driven configuration
├── routes/
│   ├── products.routes.js      # maps HTTP verbs+paths to controller functions
│   ├── users.routes.js
│   └── orders.routes.js
├── controllers/
│   ├── products.controller.js
│   ├── users.controller.js
│   └── orders.controller.js
├── services/
│   ├── products.service.js
│   ├── users.service.js
│   └── orders.service.js
├── models/
│   ├── products.model.js
│   ├── users.model.js
│   └── orders.model.js
└── tests/
```

Express doesn't enforce this split — `routes/` and `controllers/` are
sometimes merged into one file per domain when the project is small. That's
fine as long as the *service* boundary (business logic vs. everything else)
is still respected; the routes/controllers split is organizational, the
controller/service split is architectural and matters more.

## Three cross-cutting patterns that complete the split

The controller → service → model split is necessary but not sufficient —
in practice, three more patterns consistently separate a refactor that's
actually finished from one that still has loose ends. All three were
validated end-to-end on a real Flask project while building this skill;
the Node/Express column follows the same shape and should be applied the
same way when the target stack is Express instead.

### 1. Centralized configuration module

Every environment-driven value (secrets, debug flag, feature flags, API
keys) is read from **one module**, never scattered `os.environ.get()` /
`process.env.X` calls at each point of use. The rest of the app imports
that module and never touches the environment directly — this is the same
fix as playbook #2 (Externalize secrets), just applied as a standing rule
rather than a one-off patch: one hardcoded secret found during an audit
should become one shared config module, not one inline env-var read.

Python/Flask:
```python
# config.py
import os
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")
```
```python
# app.py
import config
app.config["SECRET_KEY"] = config.SECRET_KEY
```

Node/Express (using `dotenv` to load a `.env` file into `process.env`):
```javascript
// config/index.js
require('dotenv').config();

module.exports = {
  secretKey: process.env.SECRET_KEY,
  debug: process.env.NODE_ENV !== 'production',
  adminApiKey: process.env.ADMIN_API_KEY,
};
```
```javascript
// app.js
const config = require('./config');
app.set('secretKey', config.secretKey);
```
Before adding `dotenv` as a new dependency, check `package.json` — many
Express projects already declare it and simply never call `.config()` at
the entrypoint (the same "dependency exists but isn't wired up" pattern as
catalog M1).

### 2. Route registration in Router/Blueprint modules, not inline in the entrypoint

Once controllers are split by domain (playbook #8), routing should split
the same way: one router/blueprint per domain, mounted onto the app from
the entrypoint. The entrypoint's own job shrinks to "create app, mount
routers, register error handlers" — nothing else.

Python/Flask (`Blueprint`):
```python
# routes/produtos_routes.py
from flask import Blueprint
from controllers import produtos_controller

produtos_bp = Blueprint("produtos", __name__)
produtos_bp.add_url_rule("/produtos", "listar_produtos", produtos_controller.listar_produtos, methods=["GET"])
```
```python
# app.py
from routes.produtos_routes import produtos_bp
app.register_blueprint(produtos_bp)
```

Node/Express (`express.Router()`):
```javascript
// routes/products.routes.js
const express = require('express');
const productsController = require('../controllers/products.controller');

const router = express.Router();
router.get('/products', productsController.listProducts);

module.exports = router;
```
```javascript
// app.js
const productsRoutes = require('./routes/products.routes');
app.use(productsRoutes);
```
The payoff isn't just tidiness: with routing centralized per domain, adding
auth middleware to an entire domain (or to one route within it) becomes a
one-line change at the mount point instead of a change scattered across
every handler.

### 3. Centralized error handling, not a try/except in every controller

A generic `except Exception`/`catch` repeated in every controller (catalog
M2) is the same three lines copy-pasted N times: log the error, return a
generic message, don't leak internals. Once every controller does this
*consistently*, the next step is to delete the repetition and let the
framework's own centralized error path own it — one function decides what
an unhandled exception becomes, everywhere, instead of N copies of the
same decision.

Python/Flask (`@app.errorhandler`):
```python
from werkzeug.exceptions import HTTPException

@app.errorhandler(HTTPException)
def handle_http_error(e):
    return jsonify({"erro": e.description}), e.code   # keep Flask's own 404/400/405 as JSON, not HTML

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    logger.exception("Unhandled error")
    return jsonify({"erro": "Erro interno"}), 500
```
Controllers no longer need their own `try/except Exception` — an uncaught
exception now bubbles up to this handler automatically. Keep any
`try/except` that reacts *differently* to a specific exception type (e.g. a
duplicate-key error returning 409 instead of 500) — centralizing removes
the repeated generic catch-all, not deliberate, specific error handling.

Node/Express (error-handling middleware — recognized by Express via its
4-argument signature `(err, req, res, next)`, and must be registered
**last**, after every `app.use(routerX)` call):
```javascript
// registered after all routers are mounted
app.use((err, req, res, next) => {
  logger.error(err.stack);
  const status = err.statusCode || 500;
  res.status(status).json({ erro: status === 500 ? 'Erro interno' : err.message });
});
```
In Express, controllers/services signal an error by calling `next(err)`
(sync code) or by letting a rejected promise propagate out of an `async`
route handler — not by catching it locally and formatting a response
inline.

## Generalizing to other frameworks

The same three responsibilities apply even when a framework doesn't use
the words "controller" or "model": a Django view is a controller, a Django
manager/queryset method is the model layer; a Go `http.HandlerFunc` is a
controller; a Spring `@RestController` is a controller and a `@Service` is
the service layer by convention. Map onto the nearest existing convention
in the framework rather than inventing new folder names the ecosystem
doesn't recognize — MVC is about the responsibility split, not the specific
directory names above.

## When *not* to force full MVC

A trivial script or a single-endpoint utility doesn't need three layers —
forcing `services/` and `models/` folders onto five lines of code is
over-engineering in the other direction. Use judgment proportional to the
project's actual size and the number of domain entities involved; the
target layout above is for a project with multiple resources and real
business rules, which is the case this skill is built for.
