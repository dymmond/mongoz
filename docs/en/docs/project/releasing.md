---
title: Releasing Mongoz
description: Prepare, validate, publish, verify, and recover a Mongoz release through the build-once trusted-publishing workflow.
---

# Releasing Mongoz

Mongoz releases are explicit, immutable maintainer actions. Merging a version change does not
publish anything; an exact version tag on the default branch starts the release workflow.

## Release owners

| Concern | Canonical owner |
| --- | --- |
| Version | `mongoz/__init__.py` |
| Release history and GitHub release body | `docs/en/docs/release-notes.md` |
| Runtime and tooling dependencies | `pyproject.toml` |
| Package build and artifact inspection | `pyproject.toml` and `scripts/validate_package.py` |
| Tag and version validation | `scripts/release.py` |
| Publication and provenance | `.github/workflows/publish.yml` |
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
6. Merge the release-ready commit to the repository's default branch. Wait for the Python matrix,
   documentation, security, and CodSpeed workflows at that commit.

An optional release candidate uses a source version and matching tag such as `0.15.0rc1`. Each
candidate is a distinct immutable PyPI version and GitHub prerelease. A candidate does not promote
itself: prepare the stable source version and stable release-note heading in a later commit.

## Publish

Before the first trusted publication, configure PyPI with owner `dymmond`, repository `mongoz`,
workflow `publish.yml`, and environment `pypi`. Configure the GitHub `pypi` environment with
appropriate tag restrictions and required reviewers. Remove any obsolete `PYPI_TOKEN` repository
secret after the trusted publisher is confirmed.

Create an annotated tag only after the release-ready commit is on the default branch:

```console
git tag -a 0.14.0 -m "Mongoz 0.14.0"
git push origin 0.14.0
```

The workflow rejects malformed, mismatched, non-default-branch, and already-published versions. It
builds one wheel and one sdist, distributes those exact bytes to isolated acceptance jobs, attests
their provenance, publishes them with PyPI OIDC, and attaches them with checksums and committed
notes to a GitHub Release. Stable tags create stable releases; `rcN` tags create prereleases.

The final job calls the protected Render deployment hook from the `docs` environment. The Render
service must track the repository default branch and use the committed Zensical build. This
repository cannot prove the external hook, branch, or PyPI trusted-publisher settings; maintainers
must verify them before pushing the tag.

## Verify publication

- Confirm PyPI lists the intended version and both distributions.
- Download the PyPI wheel and compare its SHA-256 digest with the GitHub Release checksum.
- Verify the GitHub artifact attestation for both distributions.
- Install the package by exact version in a new environment and confirm `mongoz.__version__`.
- Confirm the GitHub Release body matches the committed version section and its prerelease flag is
  correct.
- Confirm the documentation deployment completed and the release notes and migration links resolve
  at `mongoz.dymmond.com`.

## Recovery and rollback

PyPI files and versions cannot be overwritten or edited after publication.

- If upload partially fails, inspect PyPI first. Re-run only when no conflicting filename exists;
  otherwise keep the uploaded files and finish the same version manually if safe, or yank it and
  prepare a new patch version.
- If the GitHub Release fails after PyPI succeeds, create the release from the same tag, committed
  notes, downloaded workflow artifacts, and checksums. Never rebuild the assets.
- If documentation deployment fails, leave the package and GitHub Release intact, repair the
  external deployment, and redeploy the same commit.
- If metadata is wrong or a critical regression is discovered, yank the affected PyPI version when
  appropriate, publish an advisory, and prepare a new patch release. Do not move or reuse the tag.
- If an artifact is malicious or provenance is invalid, stop the workflow, preserve evidence,
  revoke obsolete credentials, remove compromised GitHub assets where appropriate, yank the PyPI
  release, and publish a clean higher version after review.
