import unittest
from backend.database import get_db, init_db, fetch_posts, get_stats, save_post_with_tag, save_golden_tag

class TestDatabase(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_init_db_and_stats(self):
        stats = get_stats()
        self.assertIn("total_posts", stats)
        self.assertIn("golden_count", stats)
        self.assertIn("platform_counts", stats)
        self.assertIn("theme_counts", stats)
        self.assertGreaterEqual(stats["total_posts"], 0)

    def test_fetch_posts_defaults(self):
        posts = fetch_posts(limit=10)
        self.assertIsInstance(posts, list)
        if posts:
            p = posts[0]
            self.assertIn("id", p)
            self.assertIn("platform", p)
            self.assertIn("raw_text", p)
            self.assertIn("is_hand_labelled", p)

    def test_fetch_posts_filtering(self):
        posts_groww = fetch_posts(platform="Groww", limit=5)
        for p in posts_groww:
            self.assertEqual(p["platform"], "Groww")

        posts_golden = fetch_posts(status="hand_labelled", limit=5)
        for p in posts_golden:
            self.assertEqual(p["is_hand_labelled"], 1)

        posts_ai = fetch_posts(status="ai_tagged", limit=5)
        for p in posts_ai:
            self.assertEqual(p["is_hand_labelled"], 0)

    def test_save_and_fetch_golden_tag(self):
        posts = fetch_posts(limit=1)
        self.assertTrue(len(posts) > 0)
        post_id = posts[0]["id"]

        test_tag = {
            "post_id": post_id,
            "theme": "Test Verification Theme",
            "journey_stage": "Active SIP Phase",
            "what_they_did": "Continued despite dip",
            "who_they_are": "Retail investor",
            "who_can_fix_it": "Fintech Platform",
            "evidence_quote": "test quote",
            "notes": "Automated test unit"
        }
        saved = save_golden_tag(test_tag)
        self.assertEqual(saved["post_id"], post_id)
        self.assertEqual(saved["theme"], "Test Verification Theme")

    def test_search_query_resilience(self):
        # Test normal alphanumeric query
        results = fetch_posts(search_query="SIP mandate", limit=5)
        self.assertIsInstance(results, list)

        # Test query with punctuation, symbols, and malformed FTS tokens
        weird_queries = [
            "SIP NOT OR AND * ? / \\",
            "\"unclosed quote",
            "$$$ *** @@@ !!!",
            "Groww & Coin | Autopay - bounce: 100%",
            "   ",
            ""
        ]
        for q in weird_queries:
            res = fetch_posts(search_query=q, limit=5)
            self.assertIsInstance(res, list)

if __name__ == "__main__":
    unittest.main()

