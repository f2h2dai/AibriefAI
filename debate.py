# AibriefAI — إحاطة AI

Python multi-agent AI briefing pipeline with a static dashboard served from `web/`.

## Zero-cost public stack

```text
Hosting: Render Static Site free tier
Primary LLM: Google Gemini API free tier
Fallback LLM: Groq Llama 3.3 70B free tier
Pipeline: GitHub Actions scheduled every 5 minutes
Monitoring: UptimeRobot + Sentry free tier
Domain: https://aibriefai.onrender.com
```

## Local install

```bash
python -m pip install -e ".[dev]"
```

## Run with free LLM providers

```bash
export GEMINI_API_KEY=""
export GEMINI_MODEL="gemini-2.5-flash"
export GROQ_API_KEY=""
export GROQ_MODEL="llama-3.3-70b-versatile"
python scripts/run_pipeline.py --topic "AI agents" --limit 8 --emit-html
```

Missing LLM keys do not block launch. AibriefAI uses rule-based fallback when Gemini and Groq are unavailable.

## Serve dashboard locally

```bash
python -m http.server 8000 -d web
```

Open:

```text
http://localhost:8000
```

## Render deployment

```bash
git add .
git commit -m "Launch AibriefAI"
git push origin main
```

Render:

```text
New → Static Site → Connect GitHub repo → Use render.yaml → Create Static Site
```

Verify:

```bash
curl -I https://aibriefai.onrender.com
curl -fsS https://aibriefai.onrender.com/health
curl -fsS https://aibriefai.onrender.com/data/signals.json | python -m json.tool >/dev/null
```

## GitHub Actions secrets

```bash
gh secret set GEMINI_API_KEY
gh secret set GROQ_API_KEY
gh secret set SENTRY_DSN
gh secret set GITHUB_TOKEN
```

## Security scan

```bash
./scripts/secret_scan.sh
./scripts/verify_no_secret_leak.sh
```

## Verification

```bash
make verify
```
