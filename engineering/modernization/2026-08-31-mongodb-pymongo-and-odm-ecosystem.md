# MongoDB, PyMongo, and ODM ecosystem research

## 1. Task Overview

- **Task Name:** Select the supported asynchronous MongoDB foundation for Mongoz.
- **Task Description:** Verify Motor's support status, assess PyMongo Async's
  current contracts, identify MongoDB compatibility constraints, and compare
  ecosystem patterns worth adopting without cloning another ODM.
- **Assigned By:** Mongoz modernization campaign.
- **Date:** 2026-08-31.

## 2. Research Summary

- **Sources Consulted:**
  - [websearch] [Migrate from Motor to the PyMongo Async API](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/) — Motor deprecation timeline and migration mappings.
  - [websearch] [Motor 3.7.1 documentation](https://motor.readthedocs.io/en/stable/) — deprecation and critical-fix support horizon.
  - [websearch] [PyMongo release notes](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/release-notes/) — async API maturity and current driver changes.
  - [websearch] [Upgrade driver versions](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/upgrade/) — driver, Python, and MongoDB compatibility constraints.
  - [websearch] [Transactions](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/transactions/) — async session and transaction contracts.
  - [websearch] [Cursors](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/cursors/) — iteration, batching, memory, and cleanup behavior.
  - [websearch] [Bulk write](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/bulk-write/) — collection and client bulk-write capabilities.
  - [websearch] [Stable API](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/connect/connection-options/stable-api/) — server API compatibility option and MongoDB 5.0 requirement.
  - [websearch] [Monitoring](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/monitoring-and-logging/monitoring/) — command and topology observability, including redaction behavior.
  - [websearch] [Beanie](https://beanie-odm.dev/) and [Beanie migrations](https://beanie-odm.dev/tutorial/migrations/) — contemporary PyMongo Async ODM and migration ergonomics.
  - [websearch] [ODMantic engine](https://art049.github.io/odmantic/engine/) — session, transaction, and engine-level ergonomics.
  - [websearch] [MongoEngine](https://docs.mongoengine.org/) — mature synchronous ODM conventions and signals.
  - [websearch] [MongoDB integrations](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/integrations/) — official ecosystem context and raw-driver-first guidance.
  - [local git] Lilya commit `2952feb0b26addd125295ae58f584b7daa77ee77` — Zensical migration mechanics and documentation pipeline.
  - [local execution] Mongoz source, tests, package metadata, and a real MongoDB 8.2.11 container — current dependency and behavioral evidence.
- **Key Findings:**
  - Motor was deprecated on 2026-05-14 in favor of PyMongo Async. MongoDB states
    that critical fixes continue until 2027-05-14. The migration is therefore a
    current maintenance requirement, not a speculative cleanup.
  - PyMongo's async API is generally available and uses
    `pymongo.AsyncMongoClient`. A client is bound to one event loop and should be
    reused; async client/session cleanup is awaited. Motor-only loop hooks must
    not survive the migration.
  - PyMongo async `find()` returns an async cursor without awaiting the call. A
    mechanical global replacement of `await` expressions would be incorrect.
  - Transactions require sessions and a replica set or sharded deployment.
    Operations within one transaction/session must remain sequential. Mongoz's
    standalone development container cannot prove these contracts.
  - Cursor convenience methods can materialize unbounded results. Mongoz needs a
    streaming contract and explicit cleanup tests before adding ergonomics.
  - Stable API is an opt-in compatibility control requiring MongoDB 5.0 or later;
    it should not become an unconditional default before the support matrix is
    declared.
  - Beanie and ODMantic demonstrate useful transaction, projection, migration,
    and engine ergonomics. They are references, not compatibility targets.
    MongoEngine is useful for mature naming and signals but is synchronous.

## 3. Analysis

- **Alternatives Considered:**
  - **Retain Motor temporarily.** Pros: smallest immediate diff and familiar API.
    Cons: deprecated dependency, finite critical-fix window, duplicate migration
    later. Applicability: rejected for all supported runtime paths.
  - **Use PyMongo Async directly.** Pros: official driver, active support, fewer
    layers, best access to sessions, transactions, cursors, monitoring, and new
    server capabilities. Cons: some call shapes and lifecycle contracts differ
    from Motor and require focused compatibility tests. Applicability: selected.
  - **Wrap another ODM.** Pros: could acquire features quickly. Cons: conflicting
    model/query contracts, transitive policy, public-API breakage, and loss of
    Mongoz ownership. Applicability: rejected.
  - **Maintain a Motor compatibility shim.** Pros: reduces internal churn.
    Cons: preserves deprecated concepts and undermines the zero-Motor invariant.
    Applicability: rejected. Compatibility belongs at Mongoz's public boundary,
    not in a second driver facade.
- **Dependencies & Impacts:**
  - Performance: removing a redundant dependency should not itself regress the
    hot path, but cursor, pooling, and serialization benchmarks must separate
    driver/network time from Mongoz overhead.
  - Security: an actively maintained official driver improves the patch path;
    command monitoring must respect driver redaction and must not log URI secrets.
  - Maintainability: one driver and one Registry-owned lifecycle remove a major
    duplicated abstraction. Exact minimum and upper-bound policy remain a release
    decision backed by a tested matrix.
  - Compatibility: public Mongoz awaitability and result behavior should be
    preserved unless a documented defect requires a deprecation. Private Motor
    object identity is not a supported contract, but practical escape hatches
    need explicit replacement types.

## 4. Proposed Action / Recommendation

- **Recommended Option:** Replace Motor completely with PyMongo Async in Campaign
  1, with `Registry` as the canonical client lifecycle owner and focused adapter
  tests at every existing connection/database/collection seam.
- **Reasoning:**
  1. Motor is already deprecated and has a dated support horizon.
  2. PyMongo Async is the official successor and exposes the capabilities Mongoz
     needs without an extra compatibility layer.
  3. The present wrapper surface is small enough to migrate as one owner-bounded
     campaign, while query and model refactors can remain separate.
  4. Lifecycle and async-call-shape tests prevent a superficially successful
     import replacement from introducing resource or cursor defects.
- **Confidence Level:** High for the driver choice; medium for the final support
  bounds until the full PyMongo/MongoDB matrix is executed.
- **Assumptions:** Mongoz continues to support CPython 3.10–3.14 and asynchronous
  operation; documented Mongoz behavior is preserved by default; users do not
  receive a contractual guarantee that private Motor classes leak through.
- **Limitations:** Campaign 0 exercised one standalone MongoDB 8.2.11 instance.
  It did not validate replica sets, sharded clusters, authentication/TLS, network
  interruption, cancellation, pool saturation, or multiple supported driver and
  server versions.

## 5. Verification Plan

- **Tests or Validation Needed:**
  - static zero-Motor scan over source, metadata, lock files, tests, docs, and
    examples, with an allowlist only for historical migration prose;
  - unit contract tests for client construction, database/collection selection,
    awaited close, context management, and event-loop ownership;
  - real-Mongo CRUD, cursor iteration, cancellation, error, and cleanup tests;
  - replica-set session, commit, abort, retry, and sequential-operation tests;
  - Python 3.10–3.14 against a declared PyMongo/MongoDB matrix;
  - wheel installation and import smoke tests proving Motor is absent transitively;
  - before/after operation and resource benchmarks using stable data and topology.
- **Expected Results:** All current supported public behavior passes through
  PyMongo Async; no Motor package is installed; clients and cursors close reliably;
  test topology is sufficient for every capability claimed; compatibility and
  migration documentation state intentional changes precisely.

## 6. Next Steps

1. Freeze the Campaign 1 public and lifecycle contract with focused regression tests.
2. Replace the dependency and six Motor-importing source modules with PyMongo Async.
3. Add explicit Registry close/context-manager behavior and remove loop monkey-patching.
4. Validate the supported Python matrix against standalone and replica-set MongoDB.
5. Publish a migration note and attach exact zero-Motor and packaging evidence.

## 7. References & Notes

- The dates in this report follow MongoDB's official migration guide and Motor
  documentation as observed on 2026-08-31: deprecation 2026-05-14 and critical
  fixes through 2027-05-14.
- Candidate features are accepted only where they strengthen Mongoz's own public
  contract. This research does not authorize ecosystem feature parity.
- The exact dependency range must be chosen from tested compatibility evidence,
  not simply from the newest release available during implementation.
