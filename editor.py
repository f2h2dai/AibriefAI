# ── LLM (FREE TIER) ──────────────────────────────────────
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
LLM_TIMEOUT_SECONDS=25
LLM_MAX_RETRIES=3
LLM_BACKOFF_SECONDS=1

# ── DATA SOURCES (NO KEY NEEDED) ─────────────────────────
HN_BASE_URL=https://hacker-news.firebaseio.com/v0
ARXIV_BASE_URL=https://export.arxiv.org/api/query
REDDIT_BASE_URL=https://www.reddit.com
GITHUB_API_URL=https://api.github.com
GITHUB_TOKEN=          # optional, raises GitHub API rate limit

# ── SENTRY FREE TIER ─────────────────────────────────────
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.10
SENTRY_PROFILES_SAMPLE_RATE=0.0

# ── ALERT EMAIL ──────────────────────────────────────────
ALERT_EMAIL_TO=Fmg_511@hotmail.com

# ── APP ──────────────────────────────────────────────────
ENVIRONMENT=production
LOG_LEVEL=INFO
PIPELINE_INTERVAL_MINUTES=5
AIBRIEF_LLM_ENABLED=true
AIBRIEF_SLOW_RUN_SECONDS=30
AIBRIEF_HEALTH_MAX_AGE_SECONDS=600
AIBRIEF_SCORE_THRESHOLD=40
AIBRIEF_CONFIDENCE_THRESHOLD=0.60
AIBRIEF_CHECKPOINT_ENABLED=true
AIBRIEF_FAIL_FAST=true
AIBRIEF_LIMIT=8
AIBRIEF_WEB_ROOT=web
AIBRIEF_FEED_PATH=web/data/signals.json
AIBRIEF_REPORT_PATH=data/latest_report.json
AIBRIEF_HTML_BRIEF_PATH=web/brief.html
AIBRIEF_USAGE_LOG_DIR=data/usage
AIBRIEF_CACHE_DIR=.aibrief/cache
AIBRIEF_MEMORY_LOG_PATH=.aibrief/memory/aibrief_memory.md
