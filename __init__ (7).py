from __future__ import annotations

from aibrief.graph.state import AibriefState

SOCIAL_SOURCES = {"x_influencer", "reddit", "youtube"}


class QualityRiskManager:
    name = "QualityRiskManager"

    def run(self, state: AibriefState) -> AibriefState:
        for sig in state.signals:
            flags: list[str] = []
            notes: list[str] = []
            if sig.score >= 75:
                notes.append("priority: executive brief candidate")
            if sig.status != "verified":
                flags.append("below_verification_threshold")
                notes.append("hold: below verification threshold")
            if sig.confidenceScore < 0.60:
                flags.append("low_confidence")
                notes.append("hold: confidence below publication threshold")
            if sig.source in SOCIAL_SOURCES and sig.evidenceCount < 2:
                flags.append("weak_social_corroboration")
                notes.append("needs corroboration outside social engagement")
            if len(sig.title) < 20:
                flags.append("short_title")
                notes.append("needs title review")
            if not sig.url:
                flags.append("missing_source_url")
                notes.append("missing source URL")
            sig.riskFlags = flags
            sig.riskNotes = "; ".join(notes) if notes else "publishable after source review"
        state.decisions.append({"agent": self.name, "decision": "applied quality, corroboration, and publication controls"})
        return state
