# Security Policy

## Supported versions

SmartENV is pre-1.0 stable and receives security fixes on the latest released
minor version. Older versions are supported on a best-effort basis.

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes |
| < 1.0   | No  |

## Reporting a vulnerability

**Do not open a public issue for security problems.**

Report privately through GitHub Security Advisories:

<https://github.com/sc8134/SmartENV/security/advisories/new>

Please include:

- A description of the issue and its impact
- Steps to reproduce, including a minimal config file if relevant
- Affected versions and Python versions
- Any suggested fix or mitigation

You can expect an acknowledgement within 72 hours and a status update within
seven days. Once a fix is ready we will coordinate a release and credit you in
the advisory unless you prefer to remain anonymous.

## Scope

SmartENV reads configuration from files and environment variables. Issues in
scope include, but are not limited to:

- Arbitrary code execution through parsing
- Path traversal or unexpected file reads
- Denial of service through malformed input
- Secret leakage in error messages or logs

Reading a configuration file the caller explicitly passed to `load()` is
expected behavior and is not a vulnerability.
