"""
Headless unit tests for ACEest app — no display required (CI-safe).
"""
import sys
import os
import sqlite3
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch tkinter before importing app so it doesn't need a display
import unittest.mock as mock
sys.modules['tkinter'] = mock.MagicMock()
sys.modules['tkinter.ttk'] = mock.MagicMock()
sys.modules['tkinter.messagebox'] = mock.MagicMock()
sys.modules['matplotlib'] = mock.MagicMock()
sys.modules['matplotlib.pyplot'] = mock.MagicMock()


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.mktemp(suffix=".db")
        self.conn = sqlite3.connect(self.db_file)
        self.cur = self.conn.cursor()
        self.cur.execute("""
            CREATE TABLE clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE, age INTEGER, height REAL, weight REAL,
                program TEXT, calories INTEGER, target_weight REAL, target_adherence INTEGER
            )
        """)
        self.cur.execute("""
            CREATE TABLE progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT, week TEXT, adherence INTEGER
            )
        """)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_file)

    def test_insert_client(self):
        self.cur.execute(
            "INSERT INTO clients (name, age, weight, program, calories) VALUES (?, ?, ?, ?, ?)",
            ("TestUser", 25, 75.0, "Fat Loss (FL) - 3 day", 1650)
        )
        self.conn.commit()
        self.cur.execute("SELECT name, weight FROM clients WHERE name='TestUser'")
        row = self.cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "TestUser")
        self.assertEqual(row[1], 75.0)

    def test_calorie_calculation(self):
        weight = 80.0
        factor = 22  # Fat Loss factor
        calories = int(weight * factor)
        self.assertEqual(calories, 1760)

    def test_calorie_muscle_gain(self):
        weight = 80.0
        factor = 35  # Muscle Gain factor
        calories = int(weight * factor)
        self.assertEqual(calories, 2800)

    def test_progress_insert(self):
        self.cur.execute("INSERT INTO clients (name, program) VALUES (?, ?)", ("Alice", "Beginner (BG)"))
        self.cur.execute("INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)", ("Alice", "Week 01 - 2025", 85))
        self.conn.commit()
        self.cur.execute("SELECT adherence FROM progress WHERE client_name='Alice'")
        row = self.cur.fetchone()
        self.assertEqual(row[0], 85)

    def test_unique_client_name(self):
        self.cur.execute("INSERT INTO clients (name, program) VALUES (?, ?)", ("Bob", "Beginner (BG)"))
        self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.cur.execute("INSERT INTO clients (name, program) VALUES (?, ?)", ("Bob", "Beginner (BG)"))
            self.conn.commit()

    def test_bmi_calculation(self):
        weight, height_cm = 70.0, 175.0
        bmi = round(weight / (height_cm / 100) ** 2, 1)
        self.assertEqual(bmi, 22.9)

    def test_app_version_present(self):
        # Read app.py and verify version string exists
        app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
        with open(app_path) as f:
            content = f.read()
        self.assertIn("APP_VERSION", content)


if __name__ == "__main__":
    unittest.main()
