# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
*.egg-info/
dist/
build/
.venv/
venv/

# Aibrief runtime state
.aibrief/
data/usage/
*.log

# Secrets and local env files
.env
.env.*
!.env.example
!.env.production.template
*.pem
*.key
*.crt
*.p12
*.pfx
secrets.*
secret.*
*_SECRET
*_TOKEN

# Docker / local artifacts
*.tar
*.zip
Dockerfile.local
compose.override.yml

# OS/editor
.DS_Store
.idea/
.vscode/
