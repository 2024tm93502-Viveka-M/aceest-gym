from flask import Flask, request, jsonify
import sqlite3
import os
this_is_broken_on_purpose!!!

APP_VERSION = "3.0.1"
DB_NAME = os.environ.get("DB_NAME", "aceest_fitness.db")

app = Flask(__name__)

PROGRAMS = {
    "Fat Loss (FL) - 3 day":  {"factor": 22, "desc": "3-day full-body fat loss"},
    "Fat Loss (FL) - 5 day":  {"factor": 24, "desc": "5-day split, higher volume fat loss"},
    "Muscle Gain (MG) - PPL": {"factor": 35, "desc": "Push/Pull/Legs hypertrophy"},
    "Beginner (BG)":          {"factor": 26, "desc": "3-day simple beginner full-body"},
}


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE, age INTEGER, height REAL, weight REAL,
            program TEXT, calories INTEGER, target_weight REAL, target_adherence INTEGER
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT, week TEXT, adherence INTEGER
        );
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT, date TEXT, workout_type TEXT, duration_min INTEGER, notes TEXT
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT, date TEXT, weight REAL, waist REAL, bodyfat REAL
        );
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return jsonify({"app": "ACEest Fitness & Gym", "version": APP_VERSION, "status": "running"})


@app.route("/clients", methods=["POST"])
def save_client():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    program = data.get("program", "")
    if not name or program not in PROGRAMS:
        return jsonify({"error": "name and valid program are required"}), 400
    weight = data.get("weight")
    calories = int(weight * PROGRAMS[program]["factor"]) if weight else None
    conn = get_db()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO clients
            (name, age, height, weight, program, calories, target_weight, target_adherence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, data.get("age"), data.get("height"), weight,
              program, calories, data.get("target_weight"), data.get("target_adherence")))
        conn.commit()
        return jsonify({"message": f"Client '{name}' saved", "calories": calories}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/clients/<name>", methods=["GET"])
def get_client(name):
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(dict(row))


@app.route("/clients/<name>/progress", methods=["POST"])
def save_progress(name):
    data = request.get_json()
    adherence = data.get("adherence")
    week = data.get("week")
    if adherence is None or not week:
        return jsonify({"error": "adherence and week are required"}), 400
    conn = get_db()
    conn.execute("INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
                 (name, week, int(adherence)))
    conn.commit()
    conn.close()
    return jsonify({"message": "Progress saved"}), 201


@app.route("/clients/<name>/bmi", methods=["GET"])
def get_bmi(name):
    conn = get_db()
    row = conn.execute("SELECT weight, height FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    if not row or not row["weight"] or not row["height"]:
        return jsonify({"error": "Client not found or missing weight/height"}), 404
    bmi = round(row["weight"] / (row["height"] / 100) ** 2, 1)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    return jsonify({"bmi": bmi, "category": category})


@app.route("/programs", methods=["GET"])
def get_programs():
    return jsonify(PROGRAMS)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
