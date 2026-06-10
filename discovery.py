FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

RUN addgroup --system aibrief && adduser --system --ingroup aibrief aibrief

COPY pyproject.toml README.md ./
COPY aibrief ./aibrief
COPY cli ./cli
COPY scripts ./scripts
COPY web ./web
COPY data ./data
COPY main.py ./

RUN python -m pip install --upgrade pip \
    && python -m pip install . \
    && chown -R aibrief:aibrief /app

USER aibrief

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=5s --start-period=20s --retries=3 \
  CMD python - <<'PY'
import json, urllib.request
with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3) as r:
    assert r.status == 200, r.status
    assert json.loads(r.read().decode())['status'] == 'ok'
PY

CMD ["python", "-m", "aibrief.server", "--host", "0.0.0.0", "--port", "8000"]
