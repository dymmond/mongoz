---
title: Releasing Mongoz
description: Prepare, validate, publish, verify, and recover a Mongoz release through the tag-driven publishing workflow.
---

# Releasing Mongoz

Mongoz releases are explicit, immutable maintainer actions. Merging a version change does not
publish anything; an exact version tag on the default branch starts the release workflow.

## Release owners

| Concern | Canonical owner |
| --- | --- |
| Version | `mongoz/__init__.py` |
| Release history | `docs/en/docs/release-notes.md` |
| Runtime and tooling dependencies | `pyproject.toml` |
| Package build and artifact inspection | `pyproject.toml` and `scripts/validate_package.py` |
| Tag and version validation | `scripts/release.py` |
| Publication | `.github/workflows/publish.yml` and `scripts/publish` |
| Documentation source and build | `docs/en/docs`, `docs_src`, and the Zensical scripts |
| Compatibility matrix | `docs/en/docs/reference/compatibility.md` |
| Security, typing, warning, and benchmark gates | their named GitHub Actions workflows and Hatch commands |

The release environment deliberately has no lockfile. Consumer dependencies remain bounded in
`pyproject.toml`; release tools and hosted environments are pinned there or by immutable action
commit. Dependabot owns routine action updates. Update a pin through an ordinary reviewed change
and run the full release validation again.

## Prepare a release

1. Confirm the intended version follows the current Mongoz 0.x release policy. A compatibility
   expansion or migration boundary normally receives a minor version; a contained correction
   normally receives a patch version.
2. Set `__version__` once in `mongoz/__init__.py`. Do not add a version to `pyproject.toml`, the
   workflow, or the documentation configuration.
3. Keep an empty `Unreleased` section and move the prepared material under the exact version heading
   in the release notes. Summarize user-visible behavior and link to the migration guide instead of
   duplicating it.
4. Run `hatch run release:validate --check-pypi`, then `hatch run acceptance` and
   `hatch run security:audit`.
5. Review the wheel and sdist names and manifests in `dist/`. Confirm the version, README, license,
   runtime requirements, `py.typed`, and absence of generated or local material.
6. Merge the release-ready commit to the repository's default branch. Wait for the Test Suite,
   Docs Guard, CodeQL, and CodSpeed workflows at that commit.

An optional release candidate uses a source version and matching tag such as `0.15.0rc1`. Each
candidate is a distinct immutable PyPI version. A candidate does not promote itself: prepare the
stable source version and stable release-note heading in a later commit.

## Publish

Configure the repository's `PYPI_TOKEN` secret with a scoped PyPI API token and `DEPLOY_DOCS` with
the protected documentation deployment hook. Rotate both secrets according to the maintainer's
credential policy.

Create an annotated tag only after the release-ready commit is on the default branch:

```console
git tag -a 0.15.0 -m "Mongoz 0.15.0"
git push origin 0.15.0
```

The workflow builds the wheel and source distribution, checks their metadata, and calls
`scripts/publish`. That script rejects a tag that does not exactly match the canonical package
version before uploading with Twine and the scoped token. The final step calls the protected Render
deployment hook. The Render service must track the repository default branch and use the committed
Zensical build. This repository cannot prove the external hook or secret configuration;
maintainers must verify them before pushing the tag.

## Verify publication

- Confirm PyPI lists the intended version and both distributions.
- Install the package by exact version in a new environment and confirm `mongoz.__version__`.
- Confirm the documentation deployment completed and the release notes and migration links resolve
  at `mongoz.dymmond.com`.

## Recovery and rollback

PyPI files and versions cannot be overwritten or edited after publication.

- If upload partially fails, inspect PyPI first. Re-run only when no conflicting filename exists;
  otherwise keep the uploaded files and finish the same version manually if safe, or yank it and
  prepare a new patch version.
- If documentation deployment fails, leave the published package intact, repair the external
  deployment, and redeploy the same commit.
- If metadata is wrong or a critical regression is discovered, yank the affected PyPI version when
  appropriate, publish an advisory, and prepare a new patch release. Do not move or reuse the tag.
- If an artifact or publishing credential is compromised, stop the workflow, preserve evidence,
  revoke the token, yank the PyPI release when appropriate, and publish a clean higher version
  after review.
