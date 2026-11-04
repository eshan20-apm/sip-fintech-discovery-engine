import unittest
from backend.retrieval.hybrid_search import PureDenseTfidfIndex, HybridSearchEngine, hybrid_searcher

class TestRetrieval(unittest.TestCase):
    def test_pure_dense_tfidf_index(self):
        index = PureDenseTfidfIndex()
        doc_ids = ["d1", "d2", "d3"]
        docs = [
            "Market crashed and my SIP portfolio is down fifteen percent",
            "Bank deducted bounce penalty for failed mandate autopay",
            "Groww app units allocation delayed after UPI payment"
        ]
        index.fit_transform(doc_ids, docs)

        results = index.query("market crash dip portfolio", top_k=2)
        self.assertTrue(len(results) > 0)
        top_id, score = results[0]
        self.assertEqual(top_id, "d1")
        self.assertGreater(score, 0.0)

    def test_hybrid_searcher(self):
        results = hybrid_searcher.search("market crash pause cancel", limit=5)
        self.assertIsInstance(results, list)
        if results:
            first = results[0]
            self.assertIn("id", first)
            self.assertIn("raw_text", first)
            self.assertIn("rrf_score", first)
            self.assertGreater(first["rrf_score"], 0.0)

    def test_hybrid_searcher_filtering(self):
        results = hybrid_searcher.search("SIP", platform="Groww", limit=5)
        for r in results:
            self.assertEqual(r["platform"], "Groww")

if __name__ == "__main__":
    unittest.main()

