import unittest
from fastapi.testclient import TestClient
from backend.main import app

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

    def test_stats(self):
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_posts", data)
        self.assertIn("golden_count", data)

    def test_posts_query_filters(self):
        res = self.client.get("/api/posts?limit=10")
        self.assertEqual(res.status_code, 200)
        self.assertIn("posts", res.json())

        res = self.client.get("/api/posts?platform=Groww&limit=5")
        self.assertEqual(res.status_code, 200)

        res = self.client.get("/api/posts?search_query=cancel&limit=5")
        self.assertEqual(res.status_code, 200)

    def test_evaluation_endpoints(self):
        res = self.client.get("/api/evaluation/metrics")
        self.assertEqual(res.status_code, 200)
        self.assertIn("overall_kappa", res.json())

        res = self.client.get("/api/evaluation/confusion-matrix?field=theme")
        self.assertEqual(res.status_code, 200)
        self.assertIn("labels", res.json())
        self.assertIn("matrix", res.json())

        res = self.client.get("/api/evaluation/disagreements?limit=10")
        self.assertEqual(res.status_code, 200)
        self.assertIn("disagreements", res.json())

    def test_export_endpoint(self):
        # Default xlsx export
        res = self.client.get("/api/export")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertIn('filename="sip_discovery_research.xlsx"', res.headers["content-disposition"])
        self.assertGreater(len(res.content), 1000)

        # CSV export with UTF-8 BOM
        res_csv = self.client.get("/api/export?format=csv")
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.headers["content-type"], "text/csv; charset=utf-8")
        self.assertIn('filename="sip_discovery_research.csv"', res_csv.headers["content-disposition"])
        self.assertTrue(res_csv.content.startswith(b"\xef\xbb\xbf"))  # UTF-8 BOM bytes

        # Custom filename parameter with dot (e.g. 1.4) automatically protected with .xlsx
        res_custom = self.client.get("/api/export?filename=1.4")
        self.assertEqual(res_custom.status_code, 200)
        self.assertIn('filename="1.4.xlsx"', res_custom.headers["content-disposition"])

        # Custom filename parameter with existing extension does not duplicate extension
        res_custom_ext = self.client.get("/api/export?filename=1.4.xlsx")
        self.assertEqual(res_custom_ext.status_code, 200)
        self.assertIn('filename="1.4.xlsx"', res_custom_ext.headers["content-disposition"])

    def test_settings_api_key(self):
        res = self.client.post("/api/settings/api-key", json={"api_key": ""})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

    def test_research_endpoint(self):
        res = self.client.post("/api/research", json={"query": "Why do users cancel SIPs after market drop?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("posts", data)
        self.assertIn("analysis", data)

    def test_fetch_live_endpoint(self):
        res = self.client.post("/api/fetch-live", json={"query": "SIP pause", "limit_per_source": 2})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

if __name__ == "__main__":
    unittest.main()

