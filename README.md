# Docklens
Container/Docker image vulnerability scanner

A Python CLI tool that:
- Takes a Docker image
- Analyses the installed packages
- Compares them with a CVE database
- Classifies vulnerabilities by severity
- Suggests patches/upgrades
- Displays everything in a clean terminal menu

# Environnement
install devbox
```
curl -fsSL https://get.jetify.com/devbox | bash
```
run devbox
```
devbox shell
```

# Pre-commit Hooks
With every new commit, verification hooks will be executed. To bypass them, run the following command:
```
git commit -m "what my commit does blablabla" --no-verify
```
### Pre-commit tools
**pre-commit-hooks**: repository hygiene checks
- trailing whitespace, end-of-file, YAML validation, large files, etc.
-> https://github.com/pre-commit/pre-commit-hooks

**ruff**: linting + auto-fix + import sorting + code formatting
- replaces flake8, isort, and black
-> https://docs.astral.sh/ruff/

**gitleaks**: secret detection
- detects API keys, tokens, passwords (160+ secret types)
-> https://github.com/gitleaks/gitleaks

## License

This project is licensed under a Non-Commercial license.
Commercial use (including SaaS, resale, or paid services) requires prior written permission from the author.
See LICENSE for details.
