"""Bounded brief formatting over summaries produced by the existing pipeline."""

from __future__ import annotations

from aibrief.scoring.action_score import qualifies_for_act_now


NO_ACTION_TEXT = "No action required today."


def _is_saudi(signal: dict) -> bool:
    text = " ".join(
        str(signal.get(field) or "")
        for field in ("region", "topic", "title", "content", "brief_en", "brief_ar")
    ).lower()
    return "saudi" in text or "ksa" in text or "kingdom of saudi arabia" in text


class BriefComposer:
    name = "Brief Composer"

    def run(self, signals: list[dict], context: dict) -> dict:
        mode = str(context.get("mode") or "global_ai")
        threshold = float(context.get("configured_threshold", 70))
        output_signals = [dict(signal) for signal in signals]

        for signal in output_signals:
            evidence_refs = []
            for value in (signal.get("source_urls") or []) + (signal.get("evidence_urls") or []):
                if value and value not in evidence_refs:
                    evidence_refs.append(value)
            if signal.get("url") and signal["url"] not in evidence_refs:
                evidence_refs.append(signal["url"])
            signal["evidence_refs"] = evidence_refs
            signal["act_now"] = qualifies_for_act_now(signal, threshold)
            signal["x_post_draft"] = None

        fallback = None
        if mode == "saudi_act_now":
            output_signals = [signal for signal in output_signals if _is_saudi(signal) and signal["act_now"]]
            if not output_signals:
                fallback = NO_ACTION_TEXT

        return {
            "signals": output_signals,
            "output": "act_now_only" if mode == "saudi_act_now" else "full_brief",
            "fallback_text": fallback,
        }
