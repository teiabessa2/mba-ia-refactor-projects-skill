# Analysis Heuristics (Phase 1)

The goal of this phase is orientation, not judgment — figure out what's
there before deciding what's wrong with it. Everything here should be
answerable by reading files, not by guessing.

## 1. Identify the stack

Look for manifest/lockfiles first — they're unambiguous:

| Signal file | Language/ecosystem |
|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml` | Python |
| `package.json` | Node.js/JavaScript/TypeScript |
| `go.mod` | Go |
| `pom.xml`, `build.gradle` | Java/Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |

Then narrow the framework from the dependency list itself, not from
convention alone (a `package.json` can contain Express, Fastify, Koa, or
none of the above):
- Python: `flask`, `django`, `fastapi`, `bottle` in requirements + how the
  app object is constructed in the entrypoint (`Flask(__name__)`,
  `django.setup()`, `FastAPI()`).
- Node: `express`, `fastify`, `koa`, `@nestjs/core` in `package.json` +
  how routes are registered in the entrypoint.

If there's no manifest at all, infer from import/require statements across
the entrypoint and a sample of other files.

## 2. Map the request flow

Trace one representative endpoint from entry to response and note which
file handles each step:
1. Where is the route/URL registered? (entrypoint, a router file, decorators
   scattered across files?)
2. What function receives the parsed request? Does it validate input,
   call other functions, and build the response itself, or does it delegate?
3. Where does data access happen? Direct driver calls inline in the
   handler, or through a separate data-access layer?
4. Is there a distinct layer between "handle HTTP" and "touch the
   database" at all, or are they the same function?

Do this for 2-3 endpoints of different shapes (a simple read, a write with
validation, anything with a side effect like sending a notification) —
one endpoint might look fine while another is a mess.

## 3. Classify the architecture shape

Use this taxonomy to describe what you found — it drives how big the
Phase 3 restructuring will need to be:

- **Single-file monolith** — routes, handlers, data access, and startup
  config all live in one file.
- **Fat controller** — routes are split out, but handler functions contain
  business logic and direct data access inline (no service or model
  separation).
- **Fat model** — data-access functions contain business rules and
  response-shaping logic beyond persistence (the model layer is doing the
  controller's or service's job).
- **God module by domain sprawl** — layering exists (routes file,
  models file, controllers file) but one file within a layer covers every
  unrelated domain entity (e.g. one `models.py` for products, users, *and*
  orders) — see anti-pattern H3.
- **Leaky MVC** — controllers, services, and models are already separated
  as files/folders, but responsibilities cross boundaries here and there
  (some business logic still in a controller, some data shaping still in a
  model). This is the best-case starting point; Phase 3 work is targeted
  cleanup rather than a full restructure.
- **Ad-hoc scripts** — no consistent routing/handler abstraction at all
  (rare in framework-based backends, more common in minimal/custom HTTP
  servers).

## 4. Find the verification surface

Before touching anything, find out how you'll know the app still works
after a change — you'll need this in Phase 3:
- Is there a test suite? What command runs it?
- How does the app start locally? (README, `Procfile`, `docker-compose.yml`,
  a `scripts` section in `package.json`, a `Makefile`)
- Is there a health-check endpoint or an obvious smoke-test request
  (e.g. list endpoint, login) that exercises the main path?
- What does the app depend on at runtime (a database file, env vars, a
  running service) that needs to be present to actually run it, not just
  import it?

If there's no test suite, say so explicitly in the audit report — it means
Phase 3 validation will rely on manual exercise of endpoints, which is
weaker evidence and the user should know that going in.
