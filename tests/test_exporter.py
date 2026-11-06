import unittest
import io
import csv
import openpyxl
from backend.database import fetch_posts
from backend.exporter import export_posts_to_excel, export_posts_to_csv, clean_cell_val

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

    def test_export_posts_to_csv_structure(self):
        posts = fetch_posts(limit=10)
        csv_str = export_posts_to_csv(posts)
        self.assertIsInstance(csv_str, str)
        # Check UTF-8 BOM presence
        self.assertTrue(csv_str.startswith("\ufeff"))
        
        # Verify CSV readability
        reader = csv.reader(io.StringIO(csv_str.lstrip("\ufeff")))
        headers = next(reader)
        self.assertIn("Post ID", headers)
        self.assertIn("Platform", headers)
        self.assertIn("Dynamic Theme (2-3 Words)", headers)
        
        first_row = next(reader)
        self.assertEqual(len(first_row), len(headers))

    def test_clean_cell_val_removes_illegal_xml_control_chars(self):
        raw_dirty = "Groww\x00 SIP\x0b error\x08 test"
        cleaned = clean_cell_val(raw_dirty)
        self.assertEqual(cleaned, "Groww SIP error test")
        self.assertEqual(clean_cell_val(None), "")
        self.assertEqual(clean_cell_val(12345), 12345)

if __name__ == "__main__":
    unittest.main()

