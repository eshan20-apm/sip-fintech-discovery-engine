import unittest
from backend.tagger.llm_tagger import tag_post, dynamic_heuristic_tagger, analyze_research_query, validate_and_repair_quote

class TestTagger(unittest.TestCase):
    def test_dynamic_heuristic_tagger(self):
        comment = "I paused my SIP because market dropped -10% in two weeks. Feeling anxious."
        tags = dynamic_heuristic_tagger(comment)
        self.assertIn("theme", tags)
        self.assertIn("journey_stage", tags)
        self.assertIn("what_they_did", tags)
        self.assertIn("who_can_fix_it", tags)
        self.assertIn("evidence_quote", tags)
        self.assertEqual(tags["theme"], "Market dip anxiety")

    def test_zero_hallucination_evidence_quote(self):
        comment = "ICICI bank deducted 590 INR mandate bounce charge because salary got delayed by 2 days."
        tags = tag_post(comment)
        quote = tags["evidence_quote"]
        self.assertTrue(len(quote) > 0)
        self.assertIn(quote, comment, f"Evidence quote '{quote}' must be a verbatim substring of raw text")

    def test_quote_repair_fallback(self):
        raw_text = "This is a long sentence about mutual fund SIPs that fails frequently. Support does not help."
        hallucinated_quote = "this is a long sentence about mutual fund sips"
        repaired = validate_and_repair_quote(hallucinated_quote, raw_text)
        self.assertIn(repaired, raw_text)

    def test_analyze_research_query(self):
        query = "Why do Zerodha Coin investors switch to Groww?"
        analysis = analyze_research_query(query)
        self.assertIn("target_platforms", analysis)
        self.assertIn("search_keywords", analysis)
        self.assertIn("Zerodha", analysis["target_platforms"])

if __name__ == "__main__":
    unittest.main()

