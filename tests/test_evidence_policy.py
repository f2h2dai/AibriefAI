import unittest
from aibrief.evidence_policy import claim_key, freshness, is_saudi, normalize_signal

NOW = "2026-09-24T10:00:00Z"


class EvidencePolicyTests(unittest.TestCase):
    def signal(self, **extra):
        return dict(title="Saudi entity breach claim", url="https://x.com/reporter/status/123",
                    source_urls=["https://reuters.com/a", "https://agency.gov.sa/a"],
                    published_at=NOW, **extra)

    def reviews(self, signal):
        return [dict(claim_key=claim_key(signal), url=url, reviewer="editor-1", reviewed_at=NOW,
                     supports_claim=True, independence_group=str(i), primary=i == 1)
                for i, url in enumerate(signal["source_urls"])]

    def test_model_labels_and_link_counts_cannot_confirm_breach(self):
        raw = self.signal(status="verified", evidence_status="verified", evidence_count=100,
                          evidence=[dict(confirmation_state="reviewed_support", reviewer="model")])
        result = normalize_signal(raw, observed_at=NOW)
        self.assertEqual(result["evidence_status"], "unverified")
        self.assertEqual(result["evidence"][0]["observation_time"], NOW)
        self.assertEqual(result["evidence"][0]["event_time"], NOW)

    def test_review_is_exact_claim_bound_and_independent(self):
        raw = self.signal()
        reviews = self.reviews(raw)
        self.assertEqual(normalize_signal(raw, reviews=reviews)["evidence_status"], "verified")
        reviews[1]["primary"] = False
        self.assertEqual(normalize_signal(raw, reviews=reviews)["evidence_status"], "corroborated")
        reviews[1]["independence_group"] = "0"
        self.assertEqual(normalize_signal(raw, reviews=reviews)["evidence_status"], "unverified")
        reviews = self.reviews(raw)
        raw["title"] = "Different Saudi entity breach claim"
        self.assertEqual(normalize_signal(raw, reviews=reviews)["evidence_status"], "unverified")

    def test_correction_and_unreviewed_links_do_not_support(self):
        raw = self.signal()
        for change in ({"correction_url": "https://reuters.com/correction"},
                       {"supports_claim": False}, {"reviewer": ""}, {"reviewed_at": "invalid"}):
            reviews = self.reviews(raw)
            reviews[1].update(change)
            self.assertEqual(normalize_signal(raw, reviews=reviews)["evidence_status"], "unverified")

    def test_idempotence_and_arabic(self):
        raw = self.signal(reason="ادعاء غير مؤكد عن السعودية", score=90)
        normalized = normalize_signal(raw, observed_at=NOW)
        self.assertEqual(normalize_signal(normalized, observed_at=NOW), normalized)
        self.assertTrue(is_saudi({"reason": "ادعاء عن الرياض"}))
        self.assertFalse(is_saudi({"title": "KSAware unrelated product"}))

    def test_fresh_observation_cannot_refresh_old_event(self):
        self.assertEqual(freshness("2026-09-01T10:00:00Z", NOW, NOW), "stale")
        self.assertEqual(freshness(NOW, "2026-09-01T10:00:00Z", NOW), "invalid")
        self.assertEqual(freshness(None, NOW, NOW), "unknown")
        self.assertEqual(freshness("2027-01-01T00:00:00Z", NOW, NOW), "invalid")

    def test_missing_x_source_and_malformed_score_fail_closed(self):
        result = normalize_signal({"title": "Saudi breach confirmed", "source": "x", "score": "nan"})
        self.assertEqual(result["evidence_status"], "unverified")
        self.assertEqual(result["evidence"], [])
        self.assertEqual(result["score"], 0)

    def test_commentary_rank_is_capped(self):
        for raw in ({"url": "https://x.com/grok/status/123"},
                    {"url": "https://x.com/reporter/status/123", "is_reply": True}):
            self.assertEqual(normalize_signal(dict(score=100, **raw))["score"], 20)


if __name__ == "__main__":
    unittest.main()
