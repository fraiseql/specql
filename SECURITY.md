# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| < 0.4   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them to: **security@specql.dev** (or your actual email)

You should receive a response within 48 hours. If for some reason you do not, please follow up to ensure we received your original message.

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Considerations

### SQL Injection

SpecQL generates SQL code from YAML specifications. While we use parameterized queries where possible, be aware:

- **Generated PL/pgSQL functions** may contain dynamic SQL
- **Always validate** YAML input from untrusted sources
- **Review generated code** before deploying to production

### Code Generation

Generated code should be:
- **Reviewed** before deployment
- **Tested** thoroughly
- **Scanned** with security tools appropriate to the target language

### Dependencies

SpecQL uses several dependencies. We:
- Monitor for security updates
- Update dependencies regularly
- Use tools like `pip-audit` to scan for vulnerabilities

You can check dependencies yourself:
```bash
pip-audit
```

## Security Best Practices

When using SpecQL:

1. **Validate Input**: Don't generate code from untrusted YAML
2. **Review Output**: Inspect generated code before deployment
3. **Use RLS**: Leverage PostgreSQL Row-Level Security
4. **Least Privilege**: Generated database users should have minimum permissions
5. **Keep Updated**: Use the latest SpecQL version

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find similar problems
3. Prepare fixes for all supported versions
4. Release patches as soon as possible

We will credit reporters in:
- Security advisory
- Release notes
- CHANGELOG.md

Unless you prefer to remain anonymous.