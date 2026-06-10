services:
  aibrief:
    build: .
    image: aibriefai:production
    container_name: aibriefai
    env_file:
      - .env.production
    environment:
      ENVIRONMENT: production
      PORT: "8000"
      HOST: 0.0.0.0
    ports:
      - "8000:8000"
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    tmpfs:
      - /tmp:size=64m,noexec,nosuid,nodev
    healthcheck:
      test: ["CMD", "python", "-c", "import json, urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3); assert r.status == 200; assert json.loads(r.read().decode())['status'] == 'ok'"]
      interval: 60s
      timeout: 5s
      retries: 3
      start_period: 20s
