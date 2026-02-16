import sys
import os
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.dashboard.app import process_stats

class TestDashboardLogic(unittest.TestCase):

    def test_process_stats_empty(self):
        stats = {}
        df = process_stats(stats)
        self.assertTrue(df.empty)
        self.assertEqual(list(df.columns), ["Camera", "Zone", "Count"])

    def test_process_stats_valid(self):
        stats = {
            "Camera_1": {"Zone A": 10, "Zone B": 5},
            "Camera_2": {"Zone C": 8}
        }
        df = process_stats(stats)
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 3)

        # Check content
        row1 = df[(df["Camera"] == "Camera_1") & (df["Zone"] == "Zone A")].iloc[0]
        self.assertEqual(row1["Count"], 10)

        row2 = df[(df["Camera"] == "Camera_2") & (df["Zone"] == "Zone C")].iloc[0]
        self.assertEqual(row2["Count"], 8)

if __name__ == '__main__':
    unittest.main()
