# Security Policy

## Supported Versions

Schulungsplantool is in active development. Security fixes are provided for the latest published release/pre-release line only.

| Version | Supported |
|---|---|
| v0.5.0-beta.4 | ✅ Current pre-release |
| v0.5.0-beta.3 | ⚠️ Superseded pre-release |
| v0.5.0-beta.1 | ⚠️ Superseded pre-release |
| v0.4.10 | ✅ Latest stable release |
| v0.4.0–v0.4.9 | ⚠️ Superseded; update recommended |
| Older versions | ❌ |

## Reporting a Vulnerability

Do **not** open a public GitHub issue for a suspected vulnerability.

Preferred process:

1. Use GitHub **Private vulnerability reporting** / a private Security Advisory for this repository, if available.
2. Include the affected version, component/endpoint, reproduction steps, expected and actual behavior, impact, and relevant logs.
3. Do not include passwords, access tokens, private keys, production credentials, customer data or other secrets.
4. If private vulnerability reporting is unavailable, contact the repository owner privately through GitHub before publishing technical details.

## Response Targets

We aim to acknowledge a valid report within 7 days and provide a status update within 14 days. These are targets, not a contractual SLA.

## Scope

Relevant reports include, but are not limited to:

- authentication or authorization bypass;
- unintended access to project/customer data;
- unsafe project/customer file import or export;
- injection, XSS, CSRF, SSRF or path traversal;
- command/code execution;
- insecure dependency or workflow configuration;
- exposed secrets or credentials;
- tampering with signed customer-planning exchanges;
- unsafe handling of training-content or master-data Markdown;
- unintended database or Docker exposure.

## Responsible Disclosure

Please avoid destructive testing, service disruption, access to data you do not own, and public disclosure before a fix or mitigation is available.

## Secrets and Sensitive Data

Never commit or publish passwords, API tokens, private keys, production credentials or unnecessary personal/customer data. Accidentally committed secrets must be considered compromised and rotated.

## Automated Security Checks

The project uses GitHub CodeQL (Advanced Setup), automated regression tests, JavaScript/Python syntax checks and GitHub Actions workflow validation. These controls reduce risk but do not replace manual review.

CodeQL languages are explicitly restricted to:

```text
python
javascript-typescript
```

GitHub Default Setup must remain disabled so Advanced Setup can upload results without conflicts.

## Data Persistence Note

The PostgreSQL database stores product/training catalogs and the new product-bound master-data templates. Project snapshots are still carried in exported project files unless otherwise persisted by the application. Protect database backups and exported project files according to the sensitivity of the contained customer/project information.

## Release Handling

For security-relevant releases:

- update `TESTING.md` and this `SECURITY.md`;
- run the full automated suite and syntax checks;
- verify GitHub CI and CodeQL;
- push the release commit first;
- create/push the tag only after CI and CodeQL are green;
- avoid publishing unnecessary exploit detail before users have a fix.

## Current Policy Version

This policy reflects **Schulungsplantool v0.5.0-beta.4**.
