---
title: Contributing
description: Set up Mongoz development, run focused and full validation, build Zensical documentation, and preserve database-backed evidence.
---

# Contributing

Clone the repository, create an isolated Python environment, and install Hatch. The project keeps
canonical commands in `pyproject.toml` and mirrors common entry points in `Taskfile.yaml`.

## Documentation workflow

| Goal | Command |
| --- | --- |
| Prepare includes into `docs/generated` | `hatch run docs:prepare` |
| Preview with source/snippet watching | `hatch run docs:serve` |
| Strict clean-cache build | `hatch run docs:build` |
| Full docs validation | `hatch run docs:validate` |
| Remove generated docs, site, and cache | `hatch run docs:clean` |

Humans edit `docs/en/docs` and `docs_src`. `docs/generated`, `site`, and `.cache` are ephemeral and
must not be committed. Preparation writes a temporary tree and atomically replaces the generated
tree only after every source and include succeeds.

Every Python fence is syntax checked. `docs_src` examples are explicitly classified as executable,
fragment, or application-layout pseudocode; do not reclassify a broken executable example to make
the gate pass.

## Quality and runtime proof

```console
hatch run lint
hatch run format-check
hatch run typing
hatch run typing-negative
hatch run docs:validate
```

Database behavior requires the real test topology:

```console
hatch run mongodb-standalone-up
hatch run test:coverage
hatch run package:validate
hatch run mongodb-standalone-down

hatch run mongodb-replica-set-up
hatch run mongodb-replica-set-smoke
hatch run mongodb-replica-set-down
```

`hatch run acceptance` owns the complete local standalone, coverage, package, and replica-set flow.
The hosted Test Suite runs linting, typing, tests, and documentation validation across Python
3.10–3.14 as applicable. Separate Docs Guard, CodeQL, and CodSpeed workflows cover documentation
relevance, security analysis, and benchmark regressions.

## Documentation changes

Verify behavior against code, public exports, tests, and real MongoDB where server semantics matter.
Preserve historical release truth. New public behavior needs current conceptual or guide ownership,
a compact reference entry, migration guidance when observable behavior changes, and executable
evidence proportional to the claim.

Report suspected vulnerabilities privately through the GitHub Security tab as described in
`SECURITY.md`, not in a public issue.
