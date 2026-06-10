from pathlib import Path

import pytest

from aibrief.connectors.rss import FeedFetchError, parse_rss
from aibrief.default_config import DEFAULT_CONFIG, config_from_env
from aibrief.graph.aibrief_graph import AibriefAgentsGraph
from aibrief.memory.decision_log import DecisionLog
from aibrief.utils.io import write_report, write_web_feed
from aibrief.utils.text import count_keywords
from aibrief.utils.validation import ValidationError, safe_url, validate_limit, validate_topic


def base_config(tmp_path: Path, limit: int = 4) -> dict:
    config = DEFAULT_CONFIG.copy()
    config["cache_dir"] = str(tmp_path / "cache")
    config["memory_log_path"] = str(tmp_path / "memory.md")
    config["report_output_path"] = str(tmp_path / "latest_report.json")
    config["feed_output_path"] = str(tmp_path / "signals.json")
    config["html_brief_output_path"] = str(tmp_path / "brief.html")
    config["limit"] = limit
    config["llm_enabled"] = False
    return config


def test_pipeline_generates_bilingual_signals(tmp_path):
    config = base_config(tmp_path, limit=4)
    graph = AibriefAgentsGraph(config=config)
    state, decision = graph.propagate("ai-agents")
    assert len(state.signals) == 4
    assert decision["metrics"]["total_signals"] == 4
    assert all(signal.threadEn for signal in state.signals)
    assert all(signal.threadAr for signal in state.signals)
    assert all(0 <= signal.score <= 100 for signal in state.signals)
    assert all(signal.status in {"enriched", "held"} for signal in state.signals)


def test_last30days_style_enhancements_are_present(tmp_path):
    config = base_config(tmp_path, limit=6)
    config["last30days_mode"] = True
    graph = AibriefAgentsGraph(config=config)
    state, _ = graph.propagate("AI agents")
    assert state.query_plan["window"] == "last 30 days"
    assert state.query_plan["mode"] == "topic"
    assert state.metrics["total_engagement"] > 0
    assert state.metrics["best_takes"]
    assert all(signal.clusterId for signal in state.signals)


def test_validation_rejects_bad_runtime_inputs():
    with pytest.raises(ValidationError):
        validate_topic("   ")
    with pytest.raises(ValidationError):
        validate_limit(0)
    with pytest.raises(ValidationError):
        validate_limit(1000)
    assert safe_url("javascript:alert(1)") == ""
    assert safe_url("https://example.com/x#frag") == "https://example.com/x"
    assert safe_url("https://user:pass@example.com/x") == ""
    assert safe_url("http://127.0.0.1/feed") == ""
    assert safe_url("http://127.0.0.1/feed", allow_localhost=True) == "http://127.0.0.1/feed"


def test_invalid_environment_is_rejected(monkeypatch):
    monkeypatch.setenv("AIBRIEF_CONFIDENCE_THRESHOLD", "2")
    with pytest.raises(ValidationError):
        config_from_env()
    monkeypatch.delenv("AIBRIEF_CONFIDENCE_THRESHOLD")
    monkeypatch.setenv("AIBRIEF_SCORE_THRESHOLD", "abc")
    with pytest.raises(ValidationError):
        config_from_env()


def test_keyword_scoring_uses_boundaries():
    weights = {"rag": 5, "agent": 8, "agents": 8}
    assert count_keywords("storage systems", weights) == 0
    assert count_keywords("agent workflow", weights) == 8
    assert count_keywords("agents workflow", weights) == 8
    assert count_keywords("RAG retrieval", weights) == 5


def test_rss_parser_blocks_unsafe_xml():
    with pytest.raises(FeedFetchError):
        parse_rss("<!DOCTYPE rss [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><rss></rss>", "rss", 1)


def test_rss_parser_accepts_atom_links():
    xml = """<?xml version='1.0'?>
    <feed xmlns='http://www.w3.org/2005/Atom'>
      <entry><title>Agent review workflow</title><link href='https://example.com/a'/><summary>Review pipeline.</summary></entry>
    </feed>"""
    signals = parse_rss(xml, "rss", 1)
    assert len(signals) == 1
    assert signals[0].url == "https://example.com/a"
    assert signals[0].evidenceUrls == ["https://example.com/a"]


def test_atomic_outputs_include_errors(tmp_path):
    config = base_config(tmp_path, limit=2)
    graph = AibriefAgentsGraph(config=config)
    state, _ = graph.propagate("ai-agents")
    data = state.to_dict()
    data["errors"] = [{"component": "test", "message": "simulated"}]
    write_report(data, config["report_output_path"])
    write_web_feed(data, config["feed_output_path"])
    assert Path(config["report_output_path"]).exists()
    text = Path(config["feed_output_path"]).read_text(encoding="utf-8")
    assert "simulated" in text


def test_decision_log_is_size_capped(tmp_path):
    config = base_config(tmp_path, limit=2)
    state, _ = AibriefAgentsGraph(config=config).propagate("ai-agents")
    log_path = tmp_path / "memory.md"
    log = DecisionLog(str(log_path), max_bytes=10_000)
    for _ in range(20):
        log.append(state)
    assert log_path.stat().st_size <= 12_000


def test_freshness_script_uses_json_timestamp_without_git(tmp_path):
    from datetime import datetime, timezone
    from scripts.check_signals_freshness import freshness_epoch

    feed = tmp_path / "signals.json"
    feed.write_text('{"generatedAt":"' + datetime.now(timezone.utc).isoformat() + '","signals":[],"metrics":{}}', encoding="utf-8")
    epoch, source = freshness_epoch(feed)
    assert epoch is not None
    assert source == "json:generatedAt"


def test_llm_client_rejects_empty_provider_response(monkeypatch, tmp_path):
    from aibrief.utils.llm_client import LLMClient, LLMError

    client = LLMClient(gemini_api_key="dummy", groq_api_key="", max_retries=1, usage_dir=str(tmp_path))
    monkeypatch.setattr(client, "_post_json", lambda *args, **kwargs: {"candidates": [{"content": {"parts": []}}]})
    with pytest.raises(LLMError):
        client.complete(agent="qa", system="sys", prompt="prompt")


def test_rss_fetch_rejects_localhost_by_default(monkeypatch):
    from aibrief.connectors.rss import FeedFetchError, fetch_url

    monkeypatch.delenv("AIBRIEF_ALLOW_LOCAL_FEEDS", raising=False)
    with pytest.raises(FeedFetchError):
        fetch_url("http://127.0.0.1:8000/feed.xml")
