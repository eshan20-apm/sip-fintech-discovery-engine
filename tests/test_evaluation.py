import unittest
from backend.analytics.benchmark_eval import (
    calculate_cohen_kappa,
    get_kappa_interpretation,
    get_evaluation_metrics,
    get_confusion_matrix_data,
    get_disagreements,
    resolve_disagreement
)

class TestEvaluation(unittest.TestCase):
    def test_calculate_cohen_kappa_perfect(self):
        y_true = ["A", "B", "A", "B"]
        y_pred = ["A", "B", "A", "B"]
        kappa, acc = calculate_cohen_kappa(y_true, y_pred)
        self.assertEqual(kappa, 1.0)
        self.assertEqual(acc, 100.0)

    def test_calculate_cohen_kappa_chance(self):
        y_true = ["A", "B", "A", "B"]
        y_pred = ["B", "A", "B", "A"]
        kappa, acc = calculate_cohen_kappa(y_true, y_pred)
        self.assertLessEqual(kappa, 0.0)
        self.assertEqual(acc, 0.0)

    def test_kappa_interpretation(self):
        self.assertEqual(get_kappa_interpretation(0.9), "Almost Perfect")
        self.assertEqual(get_kappa_interpretation(0.65), "Substantial Agreement")
        self.assertEqual(get_kappa_interpretation(0.45), "Moderate Agreement")
        self.assertEqual(get_kappa_interpretation(-0.1), "Poor Agreement (Below Chance)")

    def test_evaluation_metrics_structure(self):
        metrics = get_evaluation_metrics()
        self.assertIn("total_benchmarked", metrics)
        self.assertIn("overall_kappa", metrics)
        self.assertIn("interpretation", metrics)
        self.assertIn("fields", metrics)
        self.assertIn("theme", metrics["fields"])
        self.assertIn("journey_stage", metrics["fields"])
        self.assertIn("what_they_did", metrics["fields"])
        self.assertIn("who_can_fix_it", metrics["fields"])

    def test_confusion_matrix_data(self):
        cm = get_confusion_matrix_data(field="theme", top_n=5)
        self.assertIn("field", cm)
        self.assertIn("labels", cm)
        self.assertIn("matrix", cm)
        self.assertEqual(len(cm["matrix"]), len(cm["labels"]))

    def test_disagreements_and_resolution(self):
        disagreements = get_disagreements(limit=10)
        self.assertIsInstance(disagreements, list)
        if disagreements:
            first = disagreements[0]
            pid = first["post_id"]
            # Test override_golden (Keep Golden Benchmark)
            ok = resolve_disagreement(pid, "override_golden")
            self.assertTrue(ok)

if __name__ == "__main__":
    unittest.main()

