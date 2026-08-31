# Mongoz modernization dossier

This directory is the durable handoff for Mongoz's engineering modernization.
It records evidence, decisions, campaign boundaries, and acceptance criteria; it
is not user documentation and is intentionally outside the generated docs tree.

## Current state

- Campaign 0, the forensic baseline, was completed on 2026-08-31.
- Mongoz is **not** modernized yet. The existing implementation remains in place.
- The first implementation campaign is the PyMongo Async driver and connection
  lifecycle cutover.
- The target dependency state is zero Motor: no runtime, optional, test, type,
  example, or compatibility-shim dependency. Historical migration notes may name
  Motor only to explain its removal.

## Documents

- [Campaign 0 forensic baseline](campaign-0-forensic-baseline.md): repository,
  architecture, API, defect, test, performance, documentation, CI, security, and
  release evidence; decisions; ordered campaign plan; and handoff.
- [MongoDB, PyMongo, and ODM ecosystem research](2026-08-31-mongodb-pymongo-and-odm-ecosystem.md): primary-source research behind the driver and feature decisions.

## Resume protocol

Before starting a campaign:

1. Read the relevant campaign section and its prerequisites.
2. Reconfirm the branch, HEAD, and working-tree state.
3. Reproduce the named defect or gap before changing its canonical owner.
4. Add focused proof, then the smallest broader proof appropriate to the risk.
5. Update this dossier with evidence and the exact commit SHA.

The repository-local `AGENTS.md` is an uncommitted working rule set. It must
remain ignored and must never be added to a commit.
