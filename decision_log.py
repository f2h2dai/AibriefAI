from __future__ import annotations

from typing import Any

from aibrief.graph.state import AibriefState
from aibrief.utils.observability import capture_exception
from aibrief.utils.text import summarize


class OpportunityResearcher:
    name = "OpportunityResearcher"

    def __init__(self, llm_client: Any | None = None):
        self.llm_client = llm_client

    def _fallback(self, content: str) -> str:
        return "Why it matters: " + summarize(content, 160) + " This can become a dashboard brief, leadership note, or technical watch item."

    def run(self, state: AibriefState) -> AibriefState:
        for sig in state.signals:
            if self.llm_client:
                try:
                    prompt = (
                        "Write a concise opportunity assessment for this AI intelligence signal. "
                        "Return 1-2 sentences, no hype, no markdown.\n\n"
                        f"Title: {sig.title}\nSource: {sig.source}\nScore: {sig.score}\nContent: {summarize(sig.content, 900)}"
                    )
                    response = self.llm_client.complete(
                        agent=self.name,
                        system="You are a senior AI intelligence analyst writing opportunity assessments.",
                        prompt=prompt,
                        max_tokens=180,
                        run_id=state.run_id,
                    )
                    sig.opportunity = response.text or self._fallback(sig.content)
                    continue
                except Exception as exc:
                    state.add_error(self.name, str(exc))
                    capture_exception(exc, agent=self.name, extra={"signal_id": sig.id})
            sig.opportunity = self._fallback(sig.content)
        state.decisions.append({"agent": self.name, "decision": "wrote opportunity arguments with free LLM / rule fallback protection"})
        return state


class SkepticResearcher:
    name = "SkepticResearcher"

    def __init__(self, llm_client: Any | None = None):
        self.llm_client = llm_client

    def _fallback(self, sig) -> str:
        warnings = []
        if sig.confidenceScore < .70:
            warnings.append("confidence below editorial threshold")
        if sig.source in {"x_influencer", "hackernews", "reddit"}:
            warnings.append("community-source signal requires corroboration")
        if not warnings:
            warnings.append("verify original source before publication")
        return "; ".join(warnings)

    def run(self, state: AibriefState) -> AibriefState:
        for sig in state.signals:
            if self.llm_client:
                try:
                    prompt = (
                        "Review this AI intelligence signal skeptically. Identify publication risks only. "
                        "Return one compact sentence.\n\n"
                        f"Title: {sig.title}\nSource: {sig.source}\nConfidence: {sig.confidenceScore}\nEvidence URLs: {', '.join(sig.evidenceUrls[:3])}\nContent: {summarize(sig.content, 900)}"
                    )
                    response = self.llm_client.complete(
                        agent=self.name,
                        system="You are a skeptical research reviewer. You flag weak evidence, source risk, and overclaiming.",
                        prompt=prompt,
                        max_tokens=180,
                        run_id=state.run_id,
                    )
                    sig.skepticism = response.text or self._fallback(sig)
                    continue
                except Exception as exc:
                    state.add_error(self.name, str(exc))
                    capture_exception(exc, agent=self.name, extra={"signal_id": sig.id})
            sig.skepticism = self._fallback(sig)
        state.decisions.append({"agent": self.name, "decision": "wrote skepticism arguments with free LLM / rule fallback protection"})
        return state
