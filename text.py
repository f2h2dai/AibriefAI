from __future__ import annotations

from typing import Any

from aibrief.graph.state import AibriefState
from aibrief.utils.observability import capture_exception
from aibrief.utils.text import arabic_brief, summarize


class BilingualEditor:
    name = "BilingualEditor"

    def __init__(self, llm_client: Any | None = None):
        self.llm_client = llm_client

    def _fallback_en(self, sig) -> str:
        take = f"\nCommunity take: {sig.bestTake}" if sig.bestTake else ""
        return (
            f"{sig.title}\n\n"
            f"Signal score: {sig.score}/100. Topic: {sig.topic}. Source: {sig.source}. "
            f"Engagement: {sig.engagement}. Evidence cluster: {sig.clusterId or 'single-source'}.\n"
            f"Summary: {summarize(sig.content, 220)}{take}\n"
            f"Opportunity: {sig.opportunity}\n"
            f"Review note: {sig.skepticism}."
        )

    def _fallback_ar(self, sig) -> str:
        return arabic_brief(sig.title, sig.score, sig.topic)

    def run(self, state: AibriefState) -> AibriefState:
        for sig in state.signals:
            if self.llm_client:
                try:
                    prompt = (
                        "Create a concise bilingual AI intelligence brief. Return strict JSON with keys threadEn and threadAr. "
                        "No markdown fences. Arabic must be natural Arabic, not transliteration.\n\n"
                        f"Title: {sig.title}\nTopic: {sig.topic}\nSource: {sig.source}\nScore: {sig.score}\n"
                        f"Summary: {summarize(sig.content, 900)}\nOpportunity: {sig.opportunity}\nSkepticism: {sig.skepticism}"
                    )
                    response = self.llm_client.complete(
                        agent=self.name,
                        system="You are a bilingual English-Arabic AI briefing editor.",
                        prompt=prompt,
                        max_tokens=550,
                        run_id=state.run_id,
                    )
                    text = response.text.strip()
                    # Avoid adding a JSON parser dependency. Extract conservatively.
                    if '"threadEn"' in text and '"threadAr"' in text:
                        import json

                        parsed = json.loads(text)
                        sig.threadEn = str(parsed.get("threadEn") or self._fallback_en(sig))[:4000]
                        sig.threadAr = str(parsed.get("threadAr") or self._fallback_ar(sig))[:4000]
                    else:
                        sig.threadEn = text[:4000] or self._fallback_en(sig)
                        sig.threadAr = self._fallback_ar(sig)
                    continue
                except Exception as exc:
                    state.add_error(self.name, str(exc))
                    capture_exception(exc, agent=self.name, extra={"signal_id": sig.id})
            sig.threadEn = self._fallback_en(sig)
            sig.threadAr = self._fallback_ar(sig)
        state.decisions.append({"agent": self.name, "decision": "generated English and Arabic briefs with free LLM / rule fallback protection"})
        return state
