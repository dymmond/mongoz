# Campaign 0: forensic baseline and modernization plan

Status: complete

Evidence date: 2026-08-31

Baseline source HEAD: `01d688e32811148da777084d31fca99cfd3444ae`

## Executive decision

Mongoz has a compact, understandable core and a real-database test suite, but it
is not production-modern by the acceptance standard of this campaign. Its green
tests coexist with a deprecated database driver, no explicit client lifecycle,
duplicate mutable query implementations, shared model metadata, incorrect index
targeting, weak type gates, invalid documentation snippets, and misleading
coverage configuration.

The first implementation campaign is a complete migration from Motor to PyMongo
Async. “Complete” means that Motor is absent from runtime and optional
dependencies, code imports, type annotations, tests, fixtures, examples, and
compatibility shims. A migration note may mention Motor historically. This takes
priority because Motor was deprecated on 2026-05-14 and its critical-fix window
ends on 2027-05-14 according to MongoDB's official migration and Motor documentation.

Campaign 0 changed engineering documentation only. It did not modernize runtime
behavior, and this dossier must not be used to claim otherwise.

## Repository state at investigation start

| Repository | Branch | HEAD | State |
| --- | --- | --- | --- |
| Mongoz | `feat/rev` | `01d688e32811148da777084d31fca99cfd3444ae` | Clean; equal to `main` and `origin/main` |
| Lilya | `feat/update_internals` | `45de8b3d8289a6f74a9a7b210ba635466d2e30a2` | Dirty: pre-existing `tests/test_requests.py` change, not touched |

A local `AGENTS.md` was created for execution discipline and excluded with
Mongoz's local `.git/info/exclude`. It is deliberately absent from commits.

## Baseline

### Runtime and dependencies

- Package version: `0.13.3` in source and built wheel metadata.
- Declared Python: `>=3.10`; classifiers cover CPython 3.10 through 3.14.
- Build backend: Hatchling.
- Runtime dependencies:
  - `motor>=3.3.1`;
  - `pydantic-settings>=2.9.0`;
  - `orjson>=3.9.5`.
- `orjson` has no import in the repository. Its necessity is unproven, and it
  failed to build in a CPython 3.14 free-threaded smoke environment because the
  available Rust toolchain was older than its build requirement. Free-threaded
  Python is not a declared support target, so this is a dependency-risk signal,
  not a supported-platform regression.
- Test and documentation dependencies are duplicated across Hatch environments.
  There is no lockfile committed for reproducible development or CI resolution.
- The active inspection environment resolved Motor 3.7.1, PyMongo 4.15.3,
  Pydantic 2.12.0, pytest 8.4.2, pytest-asyncio 0.26, mypy 1.16.1, and Ruff 0.14.

### Real database baseline

The user-started Compose environment ran MongoDB 8.2.11 as a standalone server
plus Mongo Express. The Compose file uses `mongo:latest`, fixed development
credentials, the obsolete top-level `version` field, and no health check or
replica-set initialization. The server reported maximum wire version 27.

The standalone topology is valid for present CRUD tests. It cannot validate
transactions, causal session behavior, primary failover, or replica-set retries.

### Test results

The test suite collected 237 tests and used the real `test_db` database. The
autouse fixture drops that database between tests; no mock-only test files were
found.

| Python | Result | Warnings | Duration |
| --- | ---: | ---: | ---: |
| 3.10.20 | 237 passed | 12,243 | 17.95 s |
| 3.11.15 | 237 passed | 12,243 | 5.49 s |
| 3.12.13 | 237 passed | 12,243 | 5.22 s |
| 3.13.12 | 237 passed | 12,243 | 5.44 s |
| 3.14.3 | 237 passed | 12,242 | 5.89 s |

Each row used an isolated uv environment and the same live MongoDB container.
An earlier parallel attempt incorrectly shared `.venv`; it is excluded from the
compatibility evidence. The warning total is primarily Pydantic deprecations and
field-shadow warnings. `pytest -W error` fails during import because Mongoz uses
Pydantic's deprecated `json_encoders`, scheduled for removal in Pydantic v3.

The suite is concentrated in model behavior (188 collected cases), followed by
indexes, inheritance, embedded documents, signals, databases, registry, and a
small integration group. It has no meaningful coverage of client closure,
multiple event loops, cancellation, cursor cleanup, concurrency, sessions,
transactions, network interruption, pool exhaustion, replica-set behavior, or
sharded clusters. Python-version skip markers guard versions below 3.10, which
are outside the declared support range and therefore never exercise a skip in
the supported matrix.

### Coverage

The declared coverage command uses `--cov=asyncz --cov=tests`. `asyncz` is not
imported, yet coverage reports 99% by measuring tests. This is not Mongoz source
coverage. A corrected run using `--cov=mongoz` produced:

- 2,270 statements;
- 198 missed;
- 91% aggregate source coverage;
- all 237 tests passed.

Important misses exist in Registry cleanup and driver behavior, the synchronous
runner, field paths, managers, and document paths. Campaigns must use source
coverage and branch-aware targeted assertions, not the current headline number.

### Static quality and typing

- `ruff check .` passes.
- Black check reports 57 files requiring reformatting.
- Ruff format check reports 58 files requiring reformatting.
- isort check fails across many source, test, and example files.
- mypy reports success for 48 source files, but the configuration disables
  `attr-defined`, `arg-type`, `override`, `misc`, `valid-type`, `call-overload`,
  and `no-any-return`, while allowing unparameterized generics. This is a weak
  signal rather than a strict typing guarantee.
- The checked query protocol and implementation disagree: for example, protocol
  `limit` and `skip` are async while implementations are synchronous.
- Pre-commit uses `ruff-pre-commit` 0.3.0 and permits mutating `ruff --fix`; it
  does not enforce the repository's full formatting, typing, test, docs, or
  package contract.

### Documentation

The current stack is MkDocs Material with English and Portuguese trees, include
macros, and manually maintained examples under `docs_src`.

- `hatch run docs:build` completes, but emits broken-anchor warnings in English
  and many more in Portuguese.
- Five of 40 Python files under `docs_src` do not compile:
  - `managers/custom.py`: `await` outside an async function;
  - `managers/override.py`: `await` outside an async function;
  - `managers/simple.py`: `await` outside an async function;
  - `registry/document_checks.py`: `await` outside an async function;
  - `signals/logic.py`: unmatched `)`.
- English documentation contains 41 include references and 128 Python fences,
  but no executable example or link-verification gate.
- `queries.md` exceeds 1,250 lines and mixes reference, tutorial, and advanced
  behavior. `documents.md` also owns index material. Stale language includes
  “table”/“tablename” terminology and references to Esmerald and Edgy.
- Portuguese content is incomplete and has substantial anchor drift. Removing it
  is a product/documentation policy decision, not a mechanical migration step.

### Packaging

Hatch builds `mongoz-0.13.3` wheel and source distribution. Both include the
package, `py.typed`, README, license, and project metadata. A clean CPython 3.14.3
environment installed the wheel and imported Mongoz with matching version
metadata.

The configured `build_with_check` task fails after building because Twine 6.2
rejects metadata version 2.5 emitted by the current build toolchain. Packaging is
therefore buildable but the repository's own check gate is broken. The editable
inspection environment also showed stale `0.13.0` metadata while the built wheel
was correctly `0.13.3`, demonstrating why clean installation proof matters.

### CI and release

- Tests run on Python 3.10–3.14 against `mongo:latest`.
- The lint job runs a mutating `ruff --fix` command rather than a read-only gate.
- CI has no correct source coverage, documentation, package, installation,
  security, benchmark, MongoDB-version, or replica-set gate.
- Documentation-only changes bypass the test workflow through `paths-ignore`,
  and no separate documentation workflow compensates.
- MongoDB is unpinned and has no explicit health check.
- Publishing runs from any tag using a repository token and webhook. There is no
  protected release workflow, trusted publishing/OIDC, artifact attestation, or
  pre-release convergence job.
- Action versions and Dependabot/pre-commit configuration lag Lilya's current
  repository practices. No root changelog or security policy exists.

## Architecture and canonical ownership

### Runtime map

| Domain | Current owner | Responsibility | Ownership concern |
| --- | --- | --- | --- |
| Client lifecycle | `Registry` | Creates Motor client, finds databases, tracks documents | No close/context contract; loop monkey-patch; URI retained |
| Database | `Database` | Wraps driver database and returns collections | Wrapper types are Motor-specific |
| Collection | `Collection` | Wraps driver collection | Thin but driver-specific |
| Model construction | document metaclass and `MetaInfo` | Builds Pydantic models, fields, indexes, registry links, proxies, signals | Class-level mutable metadata and import-time effects |
| Field contract | `BaseField` plus generated Pydantic `FieldInfo` subclasses | Validation and schema declaration | State duplicated/shared across inheritance |
| Primary query API | `Manager` | Django-style query building and execution | Mutable/shallow-cloned state and compilation mixed with I/O |
| Secondary query API | `QuerySet` | `Document.query` construction/execution | Duplicates Manager with divergent behavior |
| Query expressions | `Expression`, `Q`, lookup maps, manager helpers | Mongo query compilation | Multiple compilation paths and broken operators |
| Serialization | `ModelDump`, field hooks, `DocumentRow`, document methods | Python/Pydantic/BSON conversion and hydration | No single codec owner; mutation and inconsistent recursion |
| Indexes | model metadata and document class methods | Definition, inspection, creation, deletion | Target collection leaks and reconciliation can be destructive |
| Events | `Signal` and metaclass-created signal namespace | Lifecycle receiver registration and dispatch | Sync receiver accepted but dispatch assumes awaitable |
| Sync bridge | `run_sync` | Runs async work from imports/sync callers | Broad `RuntimeError` handling can mask user/runtime failures |

### Required owner convergence

1. `Registry` must exclusively own client creation, reuse, event-loop affinity,
   close, and context management.
2. Schema identity belongs to immutable per-model metadata. Operation-specific
   database/collection selection must never mutate class metadata.
3. A field declaration must be cloned per concrete model; Pydantic integration is
   an adapter to the Mongoz field contract, not a second source of truth.
4. One immutable query specification must feed one compiler and one execution
   path. `Manager` and `QuerySet` may remain public facades but cannot retain
   independent semantics.
5. One BSON codec boundary must own recursive encode/decode and hydration rules.
6. Index reconciliation must be a collection-scoped plan with explicit create,
   retain, and destructive-drop decisions.

### Coupling and debt

- Metaclass construction couples Pydantic private internals, registry mutation,
  manager binding, signals, index setup, proxy behavior, and async work.
- `MetaInfo.from_collection` is shared class state but is used as operation state.
- Public query methods mix state mutation, compilation, database calls,
  hydration, projection, and serialization.
- Raw driver objects are reachable through underscore attributes and tests, so
  they are a de facto escape hatch even though they are not a declared API.
- Assertions perform public input validation. `python -O` can remove them.
- The document registry is keyed only by class name, allowing collisions between
  models with the same name in different modules.

## MongoDB and PyMongo compatibility

Six source modules import Motor types or clients: connection Registry, Database,
Collection, document metaclass, document row hydration, and Document. Registry
constructs `AsyncIOMotorClient` and monkey-patches `get_io_loop`. The client has
no explicit close or context-manager path. `Registry.driver` resolves an
attribute named `driver` on the client rather than returning a stable driver
object, and `port` is typed as `str` despite driver ports being integers.

The selected target is `pymongo.AsyncMongoClient`, following the official
[Motor migration guide](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/).
Migration constraints include:

- no Motor loop hook or compatibility package;
- one event loop per async client and explicit awaited close;
- correct async cursor call shapes (`find()` itself is not awaited);
- session-aware operation plumbing before claiming transaction support;
- replica-set-backed transaction proof and sequential operations per session;
- explicit support bounds for Python, PyMongo, and MongoDB, derived from a matrix;
- optional Stable API only when the MongoDB >=5.0 support policy permits it;
- resource cleanup and cancellation proof for cursors and sessions.

Current Python 3.10–3.14 results prove the present dependency resolution against
one MongoDB version only. They do not establish a supported driver/server matrix.

## Public API inventory and compatibility risks

The top-level `mongoz.__all__` contract contains:

`Array`, `ArrayList`, `Binary`, `Boolean`, `Database`, `Date`, `DateTime`,
`Decimal`, `Document`, `DocumentNotFound`, `Double`, `Embed`, `Email`,
`EmbeddedDocument`, `Expression`, `fields`, `ImproperlyConfigured`, `Index`,
`IndexType`, `Integer`, `NullableObjectId`, `ForeignKey`, `Manager`,
`MongozSettings`, `MultipleDocumentsReturned`, `Object`, `ObjectId`, `Order`,
`Q`, `QuerySet`, `QuerySetManager`, `Registry`, `Signal`, `SortExpression`,
`String`, `Time`, `UUID`, `settings`, and `run_sync`.

Compatibility concerns:

- Several defined exceptions are not exported consistently, including field,
  key, and signal errors. Exception messages concatenate arguments without clear
  separators.
- Manager and QuerySet expose overlapping names but different state and iterator
  behavior. The public mental model is ambiguous.
- Protocol signatures disagree with implementations, weakening IDE/static use.
- Raw `_client` and `_collection` access is private by naming but appears in tests
  and examples. Campaign 1 must offer an explicit typed native-driver escape hatch
  or document that private object identity changes.
- Exact Motor class identity is rejected as a compatibility promise. Mongoz
  method results, awaitability, documented exceptions, and model behavior remain
  compatibility targets unless a defect is explicitly deprecated.
- There is no formal semantic-versioning, deprecation-period, or support-matrix
  policy. Campaign 6 must establish one before broad API cleanup.

## Defect ledger

“Confirmed” means reproduced by execution or direct deterministic source path.
“Strongly suspected” means the source indicates a defect but Campaign 0 did not
run a complete behavioral reproduction.

| Severity | Status | Defect and evidence/reproduction | Canonical owner | Campaign |
| --- | --- | --- | --- | --- |
| Critical | Confirmed | Motor is a required dependency and imported by six runtime modules after its 2026-05-14 deprecation. | Registry/driver boundary | 1 |
| High | Confirmed | Registry has no close/context API and patches `get_io_loop`; resource and loop ownership are undefined. | Registry | 1 |
| High | Confirmed | Hydrating from database A then B mutates class-level `Meta.from_collection`; the first instance resolves B (`mongoz_campaign0_a`, `mongoz_campaign0_b`, identity leak true). | model metadata/hydration | 3 |
| High | Confirmed | `Manager.clone()` shares filter/sort/lookup containers; filtering a clone changed the parent from `['name']` to `['name', 'score']` and list identity was true. | query state | 4 |
| High | Confirmed | `Q.nor_` compiles a nested structure containing raw `Expression` objects; MongoDB rejects it with `InvalidDocument`. | query compiler | 4 |
| High | Confirmed | Index checks using an alternate collection call create/list/drop methods without consistently forwarding it; reproduction raised MongoDB operation failure code 27. | index reconciler | 5 |
| High | Strongly suspected | Instance full-document update can overwrite concurrent field changes; no optimistic or patch-only contract exists. | persistence | 5 |
| High | Strongly suspected | Index symmetric-difference reconciliation can drop a declared index that is missing rather than create it. | index reconciler | 5 |
| Medium | Confirmed | Inherited field objects are identical across abstract, left, and right models; mutable state leaks across model classes. | field construction | 3 |
| Medium | Confirmed | `Integer(maximum=0)` accepts `1`; bound checks use truthiness, as does general custom validation for false/zero/empty values. | fields/validation | 3 |
| Medium | Confirmed | Signal registration accepts a synchronous receiver but `send()` gives its result to `gather`, raising `TypeError` instead of enforcing or adapting the contract. | signals | 6 |
| Medium | Confirmed | Lookup unwind uses the impossible condition `value and value is None`, so requested unwind never executes. | query execution | 4 |
| Medium | Confirmed | Manager and QuerySet async iteration ignore configured state such as sort/skip/limit/projection or hydration paths. | query execution | 4 |
| Medium | Confirmed | `filter_query` reuses an accumulating clause list across keyword filters, duplicating earlier clauses. | query compiler | 4 |
| Medium | Confirmed | `DocumentRow.from_row` removes `_id` from the caller-owned row dictionary. | BSON hydration | 3 |
| Medium | Confirmed | Saving a new instance delegates to `create()` without preserving an explicit collection override. | persistence | 5 |
| Medium | Confirmed | Projection occurs after fetching rather than as a MongoDB projection; this wastes bandwidth and can expose fields within the process. | query execution | 4 |
| Medium | Strongly suspected | `get_or_create` turns comparison/operator expressions into equality creation data. | query/persistence | 4 |
| Medium | Strongly suspected | Temporary update models inspect only local `__annotations__`, omit inherited fields, and silently ignore unknown keys. | persistence/validation | 3 |
| Medium | Strongly suspected | `run_sync` catches any `RuntimeError` and may retry the same awaitable in another thread, masking the actual error or reusing a coroutine. | sync bridge | 6 |
| Medium | Confirmed | Pydantic `json_encoders` deprecation makes warnings-as-errors fail and is a Pydantic v3 blocker. | serialization | 3 |
| Medium | Confirmed | Package verification fails because Twine 6.2 rejects emitted metadata 2.5. | packaging | 2 |
| Medium | Confirmed | Declared coverage measures `tests` and absent `asyncz`, producing a misleading 99% instead of Mongoz's measured 91%. | test tooling | 2 |
| Medium | Confirmed | Five documentation source examples are syntactically invalid; anchor warnings are not fatal. | docs pipeline | 8 |
| Low | Strongly suspected | Registry document names collide across modules because the key is only `__name__`. | registry/model identity | 3 |
| Low | Confirmed | Field choices are converted to a set, losing order, and grouped choices conflict with hashability even though validation anticipates groups. | fields | 3 |
| Low | Confirmed | `values` is annotated as accepting a sequence but rejects tuples unless the concrete value is a list. | query API | 4/6 |
| Low | Strongly suspected | Regex starts/ends helpers do not escape input; literal versus raw regex behavior is undocumented. | query compiler | 4/7 |

Every implementation campaign must convert its “strongly suspected” entries into
a regression test or close them as non-defects with recorded evidence.

## Missing feature decisions

| Candidate | Priority | Decision | Justification |
| --- | --- | --- | --- |
| Explicit client lifecycle and native PyMongo escape hatch | Essential | Accept | Required for correctness, cleanup, and advanced operations |
| Session plumbing and transaction ergonomics | Essential | Accept | Core MongoDB correctness boundary; must be replica-set tested |
| True database projection and streaming cursor API | Essential | Accept | Prevents waste/unbounded materialization and enables large workloads |
| Raw aggregation escape hatch plus typed common pipeline path | Important | Accept incrementally | Aggregation is core MongoDB functionality; avoid building a second language |
| Collection-level bulk write | Important | Accept | Correct high-throughput primitive; preserve driver result semantics |
| Client multi-namespace bulk write | Important | Defer | Requires newer server support and a clear multi-database contract |
| Migration framework | Important | Defer | Valuable but needs versioning/locking/rollback ownership beyond core fixes |
| Typed projections/result models | Quality | Defer to query/API campaign | Useful once one canonical query state exists |
| Stable API enabled by default | Compatibility | Reject as default | Requires MongoDB 5.0+ and would silently narrow support |
| Automatic relation loading/implicit joins | Scope | Reject | Hidden I/O and feature cloning conflict with Mongoz's explicit query model |
| Full Beanie/ODMantic/MongoEngine parity | Scope | Reject | Ecosystem informs contracts but does not define Mongoz identity |
| Parallel operations inside a transaction | Correctness | Reject | Conflicts with the driver's sequential session contract |
| Permanent Motor compatibility facade | Maintenance | Reject | Violates the zero-Motor invariant and preserves obsolete concepts |

## Testing gaps and required proof

### Unit and property tests

- immutable query state, every lookup operator, nested boolean combinations, and
  compiler output without driver execution;
- per-model field/metadata ownership, falsey validation boundaries, choices,
  recursive BSON conversion, and non-mutating hydration;
- lifecycle state machine, errors, sync bridge, signal receiver policy, and
  exception contracts;
- index plan calculation separated from destructive execution;
- property/fuzz tests for nested query and serialization inputs.

### Real MongoDB integration

- declared server-version matrix rather than `latest`;
- standalone CRUD plus replica-set sessions and transactions;
- explicit database/collection overrides with interleaved models;
- unique, compound, sparse, TTL, partial, text, and conflicting index cases;
- cursors, cancellation, early loop exit, pool cleanup, and client close;
- bulk write, aggregation, projection, concurrency, retryable errors, and network
  interruption where deterministic infrastructure supports them.

### Typing and API

- strict configuration without broad global error-code suppression;
- consumer fixtures checked as external code, including generic model/query
  inference and intentional negative cases;
- signature snapshots or API extractor for exported symbols;
- supported PyMongo types without Motor aliases or `Any` escape hatches.

### Documentation and adversarial proof

- compile and execute examples against a real server where they claim I/O;
- validate links, includes, navigation, redirects, and fenced Python syntax;
- test the installed wheel, not only the source checkout;
- attempt cancellation, receiver exceptions, duplicate model names, cross-loop
  access, concurrent writes, invalid BSON, URI redaction, and teardown failures.

## Performance baseline and methodology

Campaign 0 captured diagnostic microbenchmarks on macOS with CPython 3.14.3,
seven repeats, and no statistical environment control:

| Operation | Median-like observed time |
| --- | ---: |
| Pydantic/Mongoz model construction | 24.522 µs |
| Model dump | 1.292 µs |
| Query construction | 7.746 µs |
| Expression compilation | 2.010 µs |
| Row hydration | 30.936 µs |
| Cold-ish `hatch run ... import mongoz` | 0.27 s wall time |

These numbers are anchors, not release claims. Likely inefficiencies include
duplicate Manager/QuerySet construction, post-fetch projection, full-document
updates, repeated runtime model creation, recursive conversion with mutation, and
materialized result lists.

Campaign 7 must introduce a versioned benchmark suite (for example
pytest-benchmark and optionally CodSpeed), fixed payloads and warmup, separated
pure-Python versus driver/network measurements, controlled MongoDB topology,
distribution and memory reporting, and explicit regression budgets. Relevant
workloads are construction, expression compilation, BSON encode/decode,
hydration, bulk insert/update, projected fetch, cursor streaming, pool reuse, and
transaction overhead. No performance claim closes without raw benchmark output.

## Documentation modernization and Lilya comparison

Lilya's Zensical migration is identifiable at commit
`2952feb0b26addd125295ae58f584b7daa77ee77`. It replaced Material/MkDocs include
machinery with Zensical, generated a deterministic source tree through
`scripts/docs_pipeline.py`, added preparation/clean/build/serve commands, and
later evolved its information architecture toward getting started, concepts,
tutorials, guides, and operations. It also removed Portuguese documentation.

### Adopt, adapt, reject

| Decision | Lilya practice | Mongoz application |
| --- | --- | --- |
| Adopt | Deterministic Zensical preparation/build pipeline | Make includes and generated inputs reproducible and validate a clean build |
| Adopt | Documentation example verification and docs CI | Compile/execute snippets and build on docs-only changes |
| Adopt | Modern Python matrix, read-only format/lint gates, package tasks | Align command ownership without copying framework-specific jobs |
| Adapt | Generated source tree | Prefer ephemeral generated output unless Zensical requires tracked artifacts; declare ownership explicitly |
| Adapt | Current information architecture | Use database-domain guides: getting started, models, queries, persistence, indexes, sessions/transactions, operations, API, migration |
| Adapt | Translation removal | Decide Portuguese support and archival/redirect policy explicitly before deletion |
| Adapt | Docs guard based on public source changes | Map Mongoz's actual public modules and avoid Lilya's stale path assumptions |
| Reject | Lilya's HTTP-framework content and test partitioning | Domain-inapplicable |
| Reject | Blindly copying navigation or historical config names | Mongoz requires its own user journeys and redirects |

Proposed user-facing information architecture:

1. Start: installation, first model, first query, connection lifecycle.
2. Concepts: models/fields, registries, managers/query state, BSON identity.
3. Tutorials: CRUD application, indexes, sessions/transactions, aggregation.
4. Guides: validation, inheritance, multiple databases, performance, testing,
   production connection/security, migration from earlier Mongoz versions.
5. Reference: exported API, fields/operators/exceptions, settings, compatibility.
6. Operations: topology requirements, timeouts, monitoring, upgrades, diagnosis.

Zensical migration must preserve or redirect stable URLs, make missing anchors
fatal, establish generated-file ownership, and treat translation policy as an
explicit compatibility decision.

## Security and resilience

- `$where` is exposed and documented, permitting server-side JavaScript with
  significant security and performance implications. It needs an explicit raw,
  advanced, or rejected contract.
- Raw operator dictionaries can cross the query boundary without a documented
  trusted-input policy. User-provided web data must never be presented as safe to
  pass through directly.
- Registry retains the connection URI; logging/repr/error paths need redaction
  tests. Monitoring integrations must preserve PyMongo's event redaction.
- No first-class timeout, read/write concern, read preference, retry, TLS, or
  authentication guidance exists.
- No explicit client/cursor/session cleanup means leaks are plausible and
  cancellation behavior is unproven.
- Full-document writes and class-level collection state create concurrency and
  cross-tenant/cross-database risks.
- Public validation via `assert` disappears under optimized Python.
- There is no `SECURITY.md`, supported-version disclosure policy, dependency
  audit/SBOM, CodeQL, or release provenance.

Required security proof includes URI redaction, invalid BSON diagnostics, command
monitoring redaction, raw-query trust-boundary docs, resource teardown under
failure/cancellation, transaction abort, concurrency/lost-update tests, dependency
audit, static analysis, artifact attestations, and an adversarial review before a
release recommendation.

## Modernization decisions

1. PyMongo Async is the sole supported async driver; Motor will not remain as a
   dependency, fallback, typing package, test helper, or compatibility facade.
2. Compatibility is behavior-first. Preserve supported Mongoz public behavior;
   do not preserve private Motor object identity or confirmed defects.
3. Registry owns client lifecycle. Per-operation collection selection must be
   immutable and local to the operation.
4. Manager and QuerySet converge on one immutable query specification/compiler.
5. Serialization converges on one recursive BSON codec boundary.
6. Real MongoDB proof remains mandatory, but topology must match the claim.
7. A passing test suite, aggregate coverage, or docs build is never sufficient
   alone; warnings and supposedly generated examples are part of the gate.
8. Lilya is an engineering-practice reference, not an architecture template.
9. Documentation modernization uses Zensical only with deterministic builds,
   URL/translation decisions, and executable examples.
10. No release or version recommendation occurs until final convergence and
    adversarial acceptance are complete.

## Rejected approaches

- A mechanical Motor-to-PyMongo search/replace: async call shapes and lifecycle
  differ, so it would create silent correctness risks.
- A permanent internal compatibility layer named after Motor: it retains the
  dependency's mental model and defeats removal.
- A full rewrite: current public behavior and 237 real-database tests are useful
  assets; owner-bounded campaigns provide safer evidence.
- Broad formatting churn in behavior campaigns: it obscures reviews and makes
  regression attribution harder. Formatting convergence gets a controlled slice.
- Raising coverage by testing tests or mocks: coverage must measure Mongoz and
  important behavior must use the necessary real topology.
- Enabling Stable API unconditionally: it silently excludes MongoDB before 5.0.
- Copying ecosystem ODM APIs wholesale: features are accepted only where they
  strengthen Mongoz's identity and ownership.
- Deleting Portuguese docs as a Zensical side effect: translation support is a
  product decision with URL consequences.

## Ordered campaign plan

Each campaign is a closure boundary, not permission to widen scope. A campaign
updates this dossier with commits, evidence, remaining risks, and the next action.

### Campaign 0 — forensic baseline and dossier (complete)

- **Owner:** engineering evidence and campaign governance.
- **Scope:** repository/Lilya inspection, official research, live baseline,
  architecture/API/defect inventory, decisions, and roadmap.
- **Contract:** every major claim is labeled as measured, confirmed, suspected,
  deferred, or unproven.
- **Compatibility:** no runtime change.
- **Work and tests:** read-only investigation plus durable engineering documents;
  run current tests, matrix, source coverage, lint/type/format/docs/package/install
  checks, focused reproductions, and diagnostic benchmarks.
- **Docs:** this directory and research report.
- **Acceptance/evidence:** complete requested inventory; official source links;
  reproducible command results; coherent documentation commit; local `AGENTS.md`
  excluded from the commit.
- **Non-goals:** implementation fixes or a release claim.

### Campaign 1 — PyMongo Async and connection lifecycle

- **Canonical owner:** `Registry`, with Database/Collection as thin typed adapters.
- **Scope:** replace Motor, define client construction/reuse/close/context and
  native-driver escape hatches, update driver types and packaging.
- **Known defects/gaps:** deprecated dependency; loop monkey-patch; no close;
  ambiguous `driver`; incorrect port type; no lifecycle/cursor/cancellation proof.
- **Desired contract:** one event-loop-bound PyMongo Async client per Registry;
  explicit idempotent awaited cleanup; documented ownership; unchanged supported
  CRUD behavior; zero Motor anywhere except historical migration prose.
- **Compatibility constraints:** Python 3.10–3.14; preserve documented Mongoz
  awaitability/results; private Motor identity is not supported; exact PyMongo and
  MongoDB bounds come from executed matrix evidence.
- **Implementation:** lock regression contracts; replace dependency/imports and
  Motor-specific calls; remove `get_io_loop`; add close/context APIs; expose typed
  native objects; update test topology only as needed for lifecycle proof.
- **Required tests:** construction/options, database and collection routing, CRUD,
  find/cursor call shapes, loop affinity, close/idempotence, cancellation/error
  teardown, clean-wheel import, and zero-Motor static/install scans.
- **Required docs:** breaking/private boundary note, lifecycle examples, migration
  note, compatibility matrix, changelog entry.
- **Acceptance/evidence:** Motor absent from dependency graphs and nonhistorical
  text; all supported Python versions pass; live CRUD and lifecycle proof passes;
  wheel installs without Motor; resource warnings are clean; exact commands and
  commit SHAs recorded.
- **Non-goals:** query redesign, model metadata repair, or transaction API.

### Campaign 2 — trustworthy tooling, packaging, and test topology

- **Canonical owner:** project configuration and test infrastructure.
- **Scope:** truthful coverage, warning policy, deterministic dependencies,
  non-mutating quality gates, package verification, pinned standalone/replica-set
  services, and reusable local/CI commands.
- **Known defects/gaps:** fake 99% coverage, format/isort drift, broad mypy
  suppressions, Twine metadata failure, `mongo:latest`, no health check, no
  replica set, duplicated environments.
- **Desired contract:** one documented command per gate; local and CI semantics
  match; failures are read-only and actionable; topology matches claimed features.
- **Compatibility constraints:** keep the declared Python range unless evidence
  requires a version policy decision; do not make dependency locks part of wheel
  runtime resolution.
- **Implementation:** fix source coverage and thresholds, ratchet warnings,
  converge formatter/import tooling, update package checker, pin test images and
  health/init behavior, rationalize Hatch groups, add task orchestration where it
  removes command drift.
- **Required tests:** clean bootstrap, each supported Python, source/branch
  coverage, format/lint/type checks, sdist/wheel metadata check, clean installs,
  standalone and replica-set smoke tests.
- **Required docs:** contributor commands, topology explanation, support matrix.
- **Acceptance/evidence:** fresh checkout can reproduce every gate; no mutating CI
  checks; correct package source is measured; build/check/install all pass.
- **Non-goals:** changing domain behavior or claiming complete strict typing.

### Campaign 3 — model, field, metadata, and BSON correctness

- **Canonical owner:** immutable per-model metadata plus one BSON codec boundary.
- **Scope:** field cloning, falsey validation, inheritance, collection routing
  state, Pydantic integration, row hydration, recursive serialization, updates.
- **Known defects/gaps:** class collection leak; shared inherited fields; zero
  bounds ignored; input row mutation; Pydantic deprecated/private APIs; local-only
  annotations; choice ordering; registry collisions.
- **Desired contract:** model schemas cannot affect siblings or instances;
  validation treats falsey data correctly; hydration is non-mutating; BSON
  conversion is total and deterministic for supported nested types.
- **Compatibility constraints:** preserve serialized field names, `_id` behavior,
  default/null semantics, inheritance behavior, and documented Pydantic use unless
  a regression test proves an existing defect.
- **Implementation:** introduce per-model copied metadata/fields; operation-local
  routing; central codec; remove deprecated `json_encoders` path; explicit input
  errors instead of assertions; repair update validation and identity keys.
- **Required tests:** sibling inheritance isolation, interleaved databases,
  false/zero/empty boundaries, grouped choices, nested decimal/date/UUID/object-id
  round trips, immutable source rows, Pydantic warning gate, concurrency probes.
- **Required docs:** validation/serialization contracts, inheritance and multiple
  database guide, Pydantic compatibility and migration notes.
- **Acceptance/evidence:** each ledger item has a focused test; warnings-as-errors
  passes for owned paths; live Mongo round trips match expected BSON.
- **Non-goals:** query ergonomics, index reconciliation, or broad API renames.

### Campaign 4 — canonical immutable query engine

- **Canonical owner:** one immutable query spec, compiler, and executor.
- **Scope:** converge Manager/QuerySet behavior; cloning, expressions, lookups,
  iterator state, projection, limits/sorts/skips, result shaping, raw boundary.
- **Known defects/gaps:** shallow clone mutation; broken NOR; duplicate clauses;
  impossible unwind; iterator state loss; post-fetch projection; inconsistent
  `values`; unsafe/unclear regex and `$where`; `get_or_create` expression leakage.
- **Desired contract:** every chain returns independent state; compilation is pure;
  direct execution and async iteration share semantics; projection is server-side;
  unsupported creation predicates fail clearly.
- **Compatibility constraints:** retain Manager and QuerySet entry points as
  facades where feasible; document deliberate correction of defective outputs;
  avoid silently interpreting user text as raw regex/operators.
- **Implementation:** extract value query state and compiler; route both facades
  through it; separate compile/execute/hydrate; implement true projections and
  streaming; constrain raw escape hatches.
- **Required tests:** exhaustive operator matrix, boolean/property tests, chain
  independence, iteration parity, projection at command level, limits/sorting,
  cancellation/early exit, invalid predicate behavior, real Mongo query results.
- **Required docs:** canonical query reference, streaming/projection guide, raw
  query trust boundary, migration notes for corrected behavior.
- **Acceptance/evidence:** no duplicate semantic query implementation; all ledger
  defects reproduced then fixed; public facade parity and command evidence pass.
- **Non-goals:** sessions/transactions, index work, or a new query language.

### Campaign 5 — persistence, indexes, sessions, and advanced operations

- **Canonical owner:** operation executor for persistence/session scope and a
  separate collection-scoped index planner.
- **Scope:** patch-safe writes, collection routing, deterministic index plans,
  session/transaction plumbing, aggregation and collection bulk-write escape
  hatches.
- **Known defects/gaps:** override loss; destructive/wrong-target index behavior;
  full-document lost-update risk; no session/transaction API; no aggregation,
  true bulk, or advanced cursor contract.
- **Desired contract:** writes target the selected collection and fields;
  destructive index actions require explicit authorization; sessions flow through
  all relevant operations; transactions cleanly commit/abort; native advanced
  operations remain accessible without ODM reinvention.
- **Compatibility constraints:** standalone CRUD stays supported; transactions
  declare replica-set/sharded requirements; do not enable Stable API by default;
  multi-namespace client bulk remains deferred.
- **Implementation:** patch-oriented updates and explicit replacement path;
  calculate/apply index plans; session parameter/context support; transaction
  helper; typed aggregation/collection bulk escape hatches.
- **Required tests:** alternate collections, concurrent updates, all index kinds
  and conflicts, safe dry-run/destructive gates, replica-set commit/abort/retry,
  session propagation, aggregation, bulk partial failure and results.
- **Required docs:** index lifecycle, session/transaction/topology guide,
  concurrency semantics, aggregation/bulk patterns.
- **Acceptance/evidence:** command monitoring confirms targets/session ids;
  destructive operations are explicit; replica-set tests prove cleanup and abort;
  compatibility matrix records topology.
- **Non-goals:** schema migration framework or implicit relations.

### Campaign 6 — typing, API ergonomics, signals, and deprecations

- **Canonical owner:** exported API and compatibility policy.
- **Scope:** strict typing, generics/protocols, exceptions, signatures, signals,
  sync bridge, deprecation policy, public/native boundary.
- **Known defects/gaps:** broad mypy suppressions; protocol drift; inconsistent
  exception exports/messages; broken sync receiver acceptance; risky `run_sync`;
  no formal compatibility policy.
- **Desired contract:** external consumers receive accurate inference and stable
  documented errors; signal receiver policy is enforced; sync bridging never
  masks unrelated failures; removals have explicit deprecation windows.
- **Compatibility constraints:** additive fixes preferred; intentional breaks need
  migration instructions and release classification; Python range remains tested.
- **Implementation:** tighten types incrementally, add consumer type fixtures,
  normalize exceptions, decide async-only versus adapted signal receivers, make
  sync runner state explicit, publish compatibility/deprecation policy.
- **Required tests:** positive/negative type fixtures, API signature snapshot,
  exception messages/types, signal ordering/failure/cancellation, running-loop and
  no-loop sync cases.
- **Required docs:** complete reference, error model, signals, typing examples,
  deprecation and support policies.
- **Acceptance/evidence:** no blanket suppression for touched owners; runtime and
  protocol signatures match; public inventory diff is reviewed and explained.
- **Non-goals:** undocumented renaming churn or requiring users to import PyMongo
  for ordinary Mongoz workflows.

### Campaign 7 — performance, observability, security, and resilience

- **Canonical owner:** cross-cutting runtime policies with explicit owners for
  codec, query executor, Registry, and persistence.
- **Scope:** benchmark suite/budgets, timeout/concern controls, monitoring,
  redaction, raw-query policy, cancellation/network/pool resilience, security
  policy and dependency analysis.
- **Known defects/gaps:** diagnostic-only numbers; post-fetch/full-write overhead;
  `$where` and raw operator ambiguity; URI retention; no failure/resource proof;
  no security policy or automated analysis.
- **Desired contract:** measurable performance; secrets stay redacted; operations
  have configurable bounded behavior; cleanup is deterministic under failure;
  raw capabilities are explicit trusted APIs.
- **Compatibility constraints:** defaults should not surprise existing deployments;
  hardening changes with semantic impact need deprecation or release notes.
- **Implementation:** benchmark harness; connection/operation options; monitoring
  adapters; raw API classification; cancellation/resource fixes; `SECURITY.md`,
  dependency/static analysis, and resilience fixtures.
- **Required tests:** statistical before/after runs, memory/resource assertions,
  network fault and pool saturation, timeout/retry/concern behavior, URI/event
  redaction, optimized-Python validation, raw-query adversarial cases.
- **Required docs:** production operations/security/performance guides and
  disclosure/support policy.
- **Acceptance/evidence:** benchmark artifacts with budgets; no secret leakage;
  deterministic fault tests; security scan triaged; every claimed control tested.
- **Non-goals:** unsupported performance promises or silently filtering the full
  MongoDB expression language.

### Campaign 8 — Zensical and executable documentation

- **Canonical owner:** documentation source and deterministic build pipeline.
- **Scope:** Zensical migration, new information architecture, examples/links,
  API reference, redirects, translation decision, migration guides.
- **Known defects/gaps:** broken snippets/anchors, oversized mixed pages, stale
  framework names/terminology, partial Portuguese tree, no docs-only CI.
- **Desired contract:** every documented behavior maps to tested code; clean build
  is deterministic; examples compile and I/O examples execute; stable URLs have a
  redirect or documented break.
- **Compatibility constraints:** decide Portuguese maintenance or archival with
  users in mind; preserve search/metadata and public URLs where practical.
- **Implementation:** adapt Lilya's pipeline, keep generated ownership explicit,
  reorganize content, repair/rewrite examples, generate or maintain API reference,
  add link/include/anchor/example gates.
- **Required tests:** clean and incremental builds, link/anchor checks, fenced and
  included code compilation, real-database example execution, redirect and nav
  checks, package-doc version agreement.
- **Required docs:** the entire new user-facing structure plus migration and
  operations material produced by prior campaigns.
- **Acceptance/evidence:** zero build/link/example warnings; clean checkout build;
  docs-only CI; translation/redirect decisions recorded; operator journey review.
- **Non-goals:** copying Lilya's content or deleting translations incidentally.

### Campaign 9 — CI, release, and repository convergence

- **Canonical owner:** automation and release provenance.
- **Scope:** integrate all gates, update actions/dependencies, failure isolation,
  changelog/release metadata, protected publish workflow, trusted provenance.
- **Known defects/gaps:** unpinned MongoDB; incomplete/mutating CI; any-tag token
  publishing; no attestation, security gate, changelog, or release convergence.
- **Desired contract:** a release candidate is built once, verified across the
  declared matrix, attested, and published only from an authorized release path.
- **Compatibility constraints:** retain supported environments until matrix
  evidence and a documented release decision say otherwise.
- **Implementation:** compose CI from owner commands; least-privilege permissions;
  OIDC/trusted publishing where supported; artifact signing/attestation; changelog
  and release-note automation; docs publish after artifact acceptance.
- **Required tests:** full matrix, source coverage, strict typing/lint/format,
  standalone/replica Mongo, docs, packages/clean installs, security, benchmarks,
  action lint and dry-run release where feasible.
- **Required docs:** contributor/release runbooks, changelog, compatibility and
  migration statements, rollback procedure.
- **Acceptance/evidence:** all gates green from a clean checkout; exact artifacts
  are installed and attested; no long-lived publish token; release checklist
  completed except final adversarial acceptance.
- **Non-goals:** publishing a release before Campaign 10.

### Campaign 10 — adversarial production-readiness acceptance

- **Canonical owner:** independent acceptance review across all canonical owners.
- **Scope:** attempt to disprove correctness, compatibility, security,
  performance, documentation, and operational claims.
- **Known gaps:** any item carried by earlier handoffs; unknown unknowns surfaced
  by cross-owner and installed-artifact testing.
- **Desired contract:** every release claim survives skeptical reproduction in a
  clean environment and all material residual risks are explicit.
- **Compatibility constraints:** no late silent API breaks; failed assumptions
  return to their owner campaign.
- **Implementation:** no feature work by default; run acceptance scenarios,
  inspect source-of-truth duplication, and reopen responsible campaigns for fixes.
- **Required tests:** full release checklist plus cross-database, concurrency,
  cancellation, topology/failover, installed-wheel, docs journey, security,
  performance, and upgrade/migration exercises.
- **Required docs:** final audit, residual risks, version/release recommendation,
  operator and migration sign-off.
- **Acceptance/evidence:** clean architecture/public API/compatibility reviews;
  full verified matrix; single-owner audit; benchmark report; package provenance;
  no unresolved release blockers. Only now may a version/release be recommended.
- **Non-goals:** waiving proof because CI is green.

## Release convergence checklist

- [ ] Clean architecture and single-owner audit
- [ ] Public API inventory and compatibility review
- [ ] Full unit/property/integration/end-to-end tests
- [ ] Real standalone and replica-set MongoDB proof
- [ ] Supported Python/PyMongo/MongoDB matrix
- [ ] Strict typing and consumer fixtures
- [ ] Read-only lint, formatting, and import-order gates
- [ ] Correct source/branch coverage with meaningful thresholds
- [ ] Warning-free deterministic Zensical build
- [ ] Link, anchor, include, redirect, and executable-example proof
- [ ] sdist/wheel metadata check and clean installation smoke tests
- [ ] Zero-Motor source, metadata, environment, docs, and artifact scan
- [ ] Reproducible benchmark report and accepted regression budgets
- [ ] Security policy, dependency/static analysis, redaction/resilience proof
- [ ] Changelog, compatibility policy, migration guide, and release notes
- [ ] Least-privilege trusted publishing and artifact provenance
- [ ] Adversarial production-readiness audit

## Campaign 0 evidence commands

Representative commands used during the investigation (environment paths are
intentionally omitted where they were temporary):

```console
git status --short --branch
git rev-parse HEAD
docker compose ps
docker exec mongo mongosh --quiet --eval 'db.version()'
hatch run test:pytest
UV_PROJECT_ENVIRONMENT=<isolated> uv run --python <3.10..3.14> --extra testing pytest
hatch run test:pytest --cov=mongoz --cov-report=term-missing
hatch run test:pytest -W error
hatch run lint:style
hatch run lint:typing
hatch run docs:build
python -m compileall -q docs_src
hatch run build_with_check
python -m pip install --no-cache-dir <built-wheel>
ruff check .
ruff format --check .
black --check .
isort --check-only .
rg -n 'motor|AsyncIOMotor' .
```

Focused reproductions used temporary model/database names and directly exercised
the live server for query state, NOR compilation, collection routing, inherited
field identity, falsey bounds, and signal dispatch. These probes must become
maintained regression tests in their owning campaigns.

## Remaining risks and handoff

Campaign 0 leaves every runtime issue intentionally unresolved. The most urgent
risks are the deprecated Motor dependency and undefined client lifecycle,
followed by mutable cross-database model state, mutable query clones, destructive
index targeting, Pydantic v3 incompatibility, and absent replica-set proof.

The exact next action is to start Campaign 1 by writing focused Registry lifecycle
and existing CRUD contract tests, then replace Motor with PyMongo Async through
the six identified import seams. Do not begin with query/model refactors. The
Campaign 1 closing proof must demonstrate a clean installed wheel with no Motor
package and a repository scan whose only permitted `Motor` text is historical
migration documentation.
