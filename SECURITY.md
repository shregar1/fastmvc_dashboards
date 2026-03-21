# Security policy — fastmvc_dashboards

## Reporting a vulnerability

**Do not** open public GitHub issues for undisclosed security vulnerabilities.

Email: **sengarsinghshivansh@gmail.com**

Include:

- Short description and impact
- Steps to reproduce
- Affected versions / commits if known
- Suggested fix or patch (optional)

We aim to acknowledge receipt within a few business days.

## Supported versions

Security fixes are applied to maintained release lines; upgrade to the latest patch for your minor version when advisories are published.

## Dependency and supply chain

- Keep this package and its dependencies updated (`pip list --outdated`, Dependabot, or your org’s process).
- Do not commit secrets, API keys, or tokens; use environment variables or a secrets manager ([`fastmvc_secrets`](../fastmvc_secrets/README.md) integrates Vault / cloud backends in FastMVC apps).
- Review `pyproject.toml` and lock files in production deployments.

In the FastMVC stack, the sibling package **fastmvc_secrets** provides optional Vault / cloud secret backends for applications (see the monorepo [README](../README.md)).
