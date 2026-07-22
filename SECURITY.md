# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 2.0.x   | Yes       |
| < 2.0.0 | No        |

## Reporting a vulnerability

If you discover a security vulnerability in ForensicSuite, please report it by opening a private **Security advisory** at:

```text
https://github.com/tremolgraterol/forensicSuite/security/advisories/new
```

Alternatively, contact the maintainer directly via the email linked in the GitHub profile.

Please include:

- A clear description of the vulnerability.
- Steps to reproduce the issue.
- The affected version(s).
- Possible impact on forensic integrity or evidence handling.

## Security considerations

ForensicSuite handles sensitive evidence data. Keep the following in mind:

- Run the tool only on devices you are authorized to analyze.
- Protect GPG private keys and perito configuration files (`~/.config/forensic_suite/perito.json`).
- Verify hashes and signatures before trusting any downloaded release.
- Use hardware write blockers for judicial-grade evidence handling.
- Do not expose the daemon or any forensic output on shared/untrusted systems.

## Responsible disclosure

We follow a responsible disclosure policy. Once a report is received, we will:

1. Acknowledge receipt within 5 business days.
2. Investigate and validate the issue.
3. Work on a fix and release a patched version.
4. Coordinate public disclosure after the fix is available.

## Scope

This policy applies to the ForensicSuite source code, build scripts, GitHub Actions workflows, and released executables.

## Legal and ethical use

ForensicSuite is intended for **educational purposes and authorized forensic investigations**. Misuse of this tool is the sole responsibility of the user.
