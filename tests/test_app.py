"""
Pytest suite for ACEest Flask app — CI-safe, no display required.
"""
import pytest
import json
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from app import app as flask_app


class _NoCloseConn:
    """Wraps a sqlite3 connection and makes close() a no-op so the
    in-memory DB survives across multiple requests in the same test."""
    def __init__(self, conn):
        self._conn = conn

    def close(self):
        pass  # intentionally do nothing

    def __getattr__(self, name):
        return getattr(self._conn, name)


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE, age INTEGER, height REAL, weight REAL,
            program TEXT, calories INTEGER, target_weight REAL, target_adherence INTEGER
        );
        CREATE TABLE progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT, week TEXT, adherence INTEGER
        );
        CREATE TABLE workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT, date TEXT, workout_type TEXT, duration_min INTEGER, notes TEXT
        );
        CREATE TABLE metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT, date TEXT, weight REAL, waist REAL, bodyfat REAL
        );
    """)
    conn.commit()

    wrapped = _NoCloseConn(conn)
    app_module.get_db = lambda: wrapped

    with flask_app.test_client() as c:
        yield c

    conn.close()


def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["status"] == "running"
    assert "version" in data


def test_get_programs(client):
    res = client.get("/programs")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "Fat Loss (FL) - 3 day" in data
    assert "Beginner (BG)" in data


def test_save_client(client):
    res = client.post("/clients", json={
        "name": "TestUser", "age": 25, "height": 175.0,
        "weight": 80.0, "program": "Fat Loss (FL) - 3 day"
    })
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data["calories"] == 1760  # 80 * 22


def test_save_client_missing_fields(client):
    res = client.post("/clients", json={"name": "NoProgram"})
    assert res.status_code == 400


def test_get_client(client):
    client.post("/clients", json={
        "name": "Alice", "weight": 60.0, "program": "Beginner (BG)"
    })
    res = client.get("/clients/Alice")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["name"] == "Alice"


def test_get_client_not_found(client):
    res = client.get("/clients/Ghost")
    assert res.status_code == 404


def test_save_progress(client):
    client.post("/clients", json={"name": "Bob", "program": "Beginner (BG)"})
    res = client.post("/clients/Bob/progress", json={"week": "Week 01 - 2025", "adherence": 85})
    assert res.status_code == 201


def test_save_progress_missing_fields(client):
    res = client.post("/clients/Bob/progress", json={"adherence": 80})
    assert res.status_code == 400


def test_bmi_calculation(client):
    client.post("/clients", json={
        "name": "BmiUser", "weight": 70.0, "height": 175.0, "program": "Beginner (BG)"
    })
    res = client.get("/clients/BmiUser/bmi")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["bmi"] == 22.9
    assert data["category"] == "Normal"


def test_calorie_muscle_gain(client):
    res = client.post("/clients", json={
        "name": "MuscleUser", "weight": 80.0, "program": "Muscle Gain (MG) - PPL"
    })
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data["calories"] == 2800  # 80 * 35


def test_app_version_present():
    assert hasattr(app_module, "APP_VERSION")
    assert app_module.APP_VERSION != ""
