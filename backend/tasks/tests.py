from django.test import TestCase
from datetime import date
from .scoring import score_tasks

class TaskScoringTests(TestCase):

    def test_basic_scoring(self):
        """Test that basic scoring returns score and priority label."""
        tasks = [
            {
                "id": 1,
                "title": "Test Task",
                "due_date": date(2025, 12, 1),  # valid date object
                "estimated_hours": 2,
                "importance": 8,
                "dependencies": []
            }
        ]

        scored = score_tasks(tasks, strategy="smart_balance")

        # Must return exactly 1 task
        self.assertEqual(len(scored), 1)

        # Output must contain score + priority label
        self.assertIn("score", scored[0])
        self.assertIn("priority_label", scored[0])

        # Score must be >= 0
        self.assertGreaterEqual(scored[0]["score"], 0)

    def test_overdue_task_priority(self):
        """Overdue tasks must get higher priority than non-overdue tasks."""
        tasks = [
            {
                "id": 1,
                "title": "Overdue Task",
                "due_date": date(2020, 1, 1),  # overdue
                "estimated_hours": 2,
                "importance": 5,
                "dependencies": []
            },
            {
                "id": 2,
                "title": "Normal Task",
                "due_date": date(2025, 12, 1),  # future date
                "estimated_hours": 2,
                "importance": 5,
                "dependencies": []
            }
        ]

        scored = score_tasks(tasks, strategy="deadline_driven")

        # Extract scores by ID
        overdue_score = next(t["score"] for t in scored if t["id"] == 1)
        normal_score = next(t["score"] for t in scored if t["id"] == 2)

        # Overdue task must have a higher score
        self.assertGreater(overdue_score, normal_score)

    def test_circular_dependency_detection(self):
        """Detect cycle: 1 → 2 → 3 → 1."""
        tasks = [
            {"id": 1, "title": "A", "due_date": None, "estimated_hours": 1, "importance": 5, "dependencies": [2]},
            {"id": 2, "title": "B", "due_date": None, "estimated_hours": 1, "importance": 5, "dependencies": [3]},
            {"id": 3, "title": "C", "due_date": None, "estimated_hours": 1, "importance": 5, "dependencies": [1]},
        ]

        scored = score_tasks(tasks, strategy="smart_balance")

        # Concatenate all issues text
        all_issues = " ".join(
            " ".join(t["issues"]) for t in scored
        )

        # Must detect cycle
        self.assertIn("Circular dependency detected", all_issues)
