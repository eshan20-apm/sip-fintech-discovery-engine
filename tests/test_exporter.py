import unittest
from backend.database import fetch_posts
from backend.exporter import export_posts_to_excel
import openpyxl
import io

class TestExporter(unittest.TestCase):
    def test_export_posts_to_excel_structure(self):
        posts = fetch_posts(limit=10)
        excel_bytes = export_posts_to_excel(posts)
        self.assertIsInstance(excel_bytes, bytes)
        self.assertGreater(len(excel_bytes), 1000)

        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))
        self.assertEqual(len(wb.sheetnames), 3)
        self.assertIn("Active Research Feed", wb.sheetnames)
        self.assertIn("Golden Benchmark Set", wb.sheetnames)
        self.assertIn("Reliability & Kappa Metrics", wb.sheetnames)

        ws1 = wb["Active Research Feed"]
        self.assertGreater(ws1.max_row, 1)
        self.assertEqual(ws1.cell(row=1, column=1).value, "Post ID")

        ws3 = wb["Reliability & Kappa Metrics"]
        self.assertGreater(ws3.max_row, 5)

if __name__ == "__main__":
    unittest.main()

