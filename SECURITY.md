# Security policy

## Supported versions

Security fixes are made on the latest maintained Mongoz 0.x release line and
the default development branch. Older releases should be
upgraded to the latest release before a report is assessed. Maintainers may
announce a backport when the affected population or upgrade risk justifies one.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use this
repository's **Security** tab and choose **Report a vulnerability** to open a
private GitHub security advisory with the maintainers.

Include the affected Mongoz and Python versions, a minimal reproducer, expected
and observed behavior, impact, and any relevant MongoDB/PyMongo configuration.
Avoid including real credentials, production data, or other people's personal
information. The maintainers will coordinate validation, remediation, and
disclosure through the private advisory.

## Security boundaries

Mongoz validates and serializes declared document fields and preserves native
PyMongo failures. It is not an HTTP authentication, authorization, tenant
isolation, or request-validation layer. Applications remain responsible for
those controls and for database accounts, TLS, network policy, secrets,
timeouts, resource limits, and safe operational monitoring.

The following are privileged developer-facing escape hatches and must not
receive unvalidated request data: raw filter dictionaries and expressions,
regular-expression patterns, aggregation pipelines, `$where` JavaScript, bulk
write operations, and native PyMongo client/database/collection access.

MongoDB and PyMongo own BSON size/type limits, topology behavior, retryable
reads and writes, read/write concerns, server selection, and native error
redaction. Mongoz must pass those contracts through without weakening them.

## Dependency policy

Runtime dependencies are kept intentionally small and constrained to supported
major versions where compatibility evidence exists. Automated dependency
updates, dependency review, vulnerability auditing, and CodeQL provide
repository-visible checks. Reports involving a dependency are welcome when the
issue is reachable through Mongoz; upstream-only issues may also need to be
reported privately to the upstream project.
