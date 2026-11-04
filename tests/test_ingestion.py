import unittest
from backend.ingestion.dedup import is_spam, is_spam_or_promotional, deduplicate_posts
from backend.ingestion.hinglish import detect_hinglish, get_hinglish_context_hint, enrich_with_hinglish_context, enrich_hinglish_context
from backend.ingestion.normalizer import clean_text, anonymize_text, generate_post_id

class TestIngestion(unittest.TestCase):
    def test_spam_detection(self):
        self.assertTrue(is_spam("Join my telegram group t.me/profit123 for calls"))
        self.assertTrue(is_spam("Call me on whatsapp group link for tips"))
        self.assertTrue(is_spam("short text"))  # less than 20 chars
        self.assertFalse(is_spam("Why did Groww debit Rs 5000 twice for my monthly SIP mandate?"))
        self.assertTrue(is_spam_or_promotional("t.me/cryptosignals daily profit guaranteed"))

    def test_deduplication(self):
        raw_list = [
            {"id": "p1", "raw_text": "I want to cancel my Groww SIP because market is crashing down", "platform": "Groww", "source": "playstore"},
            {"id": "p2", "raw_text": "I want to cancel my Groww SIP because market is crashing down", "platform": "Groww", "source": "playstore"},
            {"id": "p3", "raw_text": "Join telegram channel t.me/forextrading daily 100% profit guarantee now", "platform": "Groww", "source": "playstore"},
            {"id": "p4", "raw_text": "Zerodha Coin does not provide direct SOA mutual fund statements easily", "platform": "Zerodha", "source": "reddit"},
        ]
        clean, dropped = deduplicate_posts(raw_list, similarity_threshold=0.8)
        self.assertEqual(len(clean), 2)
        self.assertEqual(dropped, 2)

    def test_hinglish_normalization(self):
        sample = "Mera paisa cut gaya but units allocate nahi hue Groww app me"
        self.assertTrue(detect_hinglish(sample))
        hint = get_hinglish_context_hint(sample)
        self.assertIn("money debited", hint.lower())
        info = enrich_with_hinglish_context(sample)
        self.assertTrue(info["detected"])
        self.assertEqual(info["theme"], "Units allocation delay")

        alias_info = enrich_hinglish_context(sample)
        self.assertEqual(alias_info["theme"], "Units allocation delay")

    def test_normalizer(self):
        raw = "Contact me at user@example.com or +91 9876543210 regarding issue"
        cleaned = clean_text(raw)
        anonymized = anonymize_text(cleaned)
        self.assertNotIn("user@example.com", anonymized)
        self.assertNotIn("9876543210", anonymized)
        self.assertIn("[REDACTED_EMAIL]", anonymized)
        self.assertIn("[REDACTED_PHONE]", anonymized)

        pid = generate_post_id("Groww", "playstore", anonymized)
        self.assertTrue(pid.startswith("POST_GROWW_"))

if __name__ == "__main__":
    unittest.main()
