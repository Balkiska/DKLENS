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

# Auto-activation (direnv)
The devbox environment activates automatically when entering the repository directory.
This requires a **one-time setup per machine**:
```
sudo apt install direnv
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
source ~/.bashrc
direnv allow
```
After that, opening the repository directory will activate the environment automatically.

## License

This project is licensed under a Non-Commercial license.
Commercial use (including SaaS, resale, or paid services) requires prior written permission from the author.
See LICENSE for details.
