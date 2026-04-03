import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, date
import matplotlib.pyplot as plt

APP_VERSION = "2.0.0"
DB_NAME = "aceest_fitness.db"


class ACEestApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"ACEest Fitness & Performance v{APP_VERSION}")
        self.root.geometry("1300x850")
        self.root.configure(bg="#1a1a1a")

        self.conn = None
        self.cur = None
        self.current_client = None

        self.init_db()
        self.setup_data()
        self.setup_ui()
        self.refresh_client_list()

    def init_db(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cur = self.conn.cursor()

        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
        exists = self.cur.fetchone() is not None
        if exists:
            self.cur.execute("PRAGMA table_info(clients)")
            cols = [row[1] for row in self.cur.fetchall()]
            required = {"id", "name", "age", "height", "weight", "program", "calories", "target_weight", "target_adherence"}
            if not required.issubset(set(cols)):
                self.cur.execute("DROP TABLE clients")

        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE, age INTEGER, height REAL, weight REAL,
                program TEXT, calories INTEGER, target_weight REAL, target_adherence INTEGER
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT, week TEXT, adherence INTEGER
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT, date TEXT, workout_type TEXT, duration_min INTEGER, notes TEXT
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_id INTEGER, name TEXT, sets INTEGER, reps INTEGER, weight REAL
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT, date TEXT, weight REAL, waist REAL, bodyfat REAL
            )
        """)
        self.conn.commit()

    def setup_data(self):
        self.programs = {
            "Fat Loss (FL) - 3 day": {"factor": 22, "desc": "3-day full-body fat loss"},
            "Fat Loss (FL) - 5 day": {"factor": 24, "desc": "5-day split, higher volume fat loss"},
            "Muscle Gain (MG) - PPL": {"factor": 35, "desc": "Push/Pull/Legs hypertrophy"},
            "Beginner (BG)": {"factor": 26, "desc": "3-day simple beginner full-body"},
        }

    def setup_ui(self):
        tk.Label(self.root, text=f"ACEest Functional Fitness System v{APP_VERSION}",
                 bg="#d4af37", fg="black", font=("Helvetica", 24, "bold"), height=2).pack(fill="x")

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.root, textvariable=self.status_var, bg="#111111", fg="#d4af37", anchor="w").pack(side="bottom", fill="x")

        main = tk.Frame(self.root, bg="#1a1a1a")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.LabelFrame(main, text=" Client Management ", bg="#1a1a1a", fg="#d4af37", font=("Arial", 12, "bold"))
        left.pack(side="left", fill="y", padx=10, pady=5)

        tk.Label(left, text="Select Client", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.client_list = ttk.Combobox(left, state="readonly")
        self.client_list.pack(pady=(0, 5))
        self.client_list.bind("<<ComboboxSelected>>", self.on_client_selected)

        for label, var_name, var_type in [
            ("Name", "name", tk.StringVar), ("Age", "age", tk.IntVar),
            ("Height (cm)", "height", tk.DoubleVar), ("Weight (kg)", "weight", tk.DoubleVar),
        ]:
            tk.Label(left, text=label, bg="#1a1a1a", fg="white").pack(pady=(5, 0))
            var = var_type()
            setattr(self, var_name, var)
            tk.Entry(left, textvariable=var, bg="#333", fg="white").pack()

        tk.Label(left, text="Program", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.program = tk.StringVar()
        ttk.Combobox(left, textvariable=self.program, values=list(self.programs.keys()), state="readonly").pack()

        tk.Label(left, text="Target Weight (kg)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        self.target_weight = tk.DoubleVar()
        tk.Entry(left, textvariable=self.target_weight, bg="#333", fg="white").pack()

        tk.Label(left, text="Target Adherence %", bg="#1a1a1a", fg="white").pack(pady=(5, 0))
        self.target_adherence = tk.IntVar()
        tk.Entry(left, textvariable=self.target_adherence, bg="#333", fg="white").pack()

        tk.Label(left, text="Weekly Adherence %", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        self.adherence = tk.IntVar(value=0)
        ttk.Scale(left, from_=0, to=100, orient="horizontal", variable=self.adherence).pack(pady=(0, 5))

        for text, cmd in [
            ("Save Client", self.save_client), ("Load Client", self.load_client),
            ("Save Weekly Progress", self.save_progress), ("Log Workout", self.open_log_workout_window),
            ("Log Body Metrics", self.open_log_metrics_window), ("View Workout History", self.open_workout_history_window),
        ]:
            ttk.Button(left, text=text, command=cmd).pack(pady=5)

        right = tk.Frame(main, bg="#1a1a1a")
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        summary_frame = tk.Frame(notebook, bg="#1a1a1a")
        notebook.add(summary_frame, text="Client Summary")
        self.summary = tk.Text(summary_frame, bg="#111", fg="white", font=("Consolas", 11))
        self.summary.pack(fill="both", expand=True, padx=10, pady=10)

        analytics_frame = tk.Frame(notebook, bg="#1a1a1a")
        notebook.add(analytics_frame, text="Progress & Analytics")
        for text, cmd in [
            ("Adherence Chart", self.show_progress_chart),
            ("Weight Trend Chart", self.show_weight_chart),
            ("BMI & Risk Info", self.show_bmi_info),
        ]:
            ttk.Button(analytics_frame, text=text, command=cmd).pack(pady=10)

    def refresh_client_list(self):
        self.cur.execute("SELECT name FROM clients ORDER BY name")
        names = [row[0] for row in self.cur.fetchall()]
        self.client_list["values"] = names
        if self.current_client in names:
            self.client_list.set(self.current_client)

    def on_client_selected(self, event=None):
        name = self.client_list.get()
        if name:
            self.name.set(name)
            self.current_client = name
            self.load_client()

    def set_status(self, text):
        self.status_var.set(text)

    def save_client(self):
        if not self.name.get() or not self.program.get():
            messagebox.showerror("Error", "Name and Program are required")
            return
        name = self.name.get().strip()
        weight = self.weight.get() if self.weight.get() > 0 else None
        factor = self.programs[self.program.get()]["factor"]
        calories = int(weight * factor) if weight else None
        try:
            self.cur.execute("""
                INSERT OR REPLACE INTO clients
                (name, age, height, weight, program, calories, target_weight, target_adherence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, self.age.get() or None, self.height.get() or None, weight,
                  self.program.get(), calories,
                  self.target_weight.get() or None, self.target_adherence.get() or None))
            self.conn.commit()
            self.current_client = name
            self.refresh_client_list()
            self.set_status(f"Saved client: {name}")
            messagebox.showinfo("Saved", "Client data saved")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def load_client(self):
        name = self.name.get().strip() or self.client_list.get()
        if not name:
            messagebox.showwarning("No Client", "Enter or select client name first")
            return
        self.cur.execute("SELECT * FROM clients WHERE name=?", (name,))
        row = self.cur.fetchone()
        if not row:
            messagebox.showwarning("Not Found", "Client not found")
            return
        _, name, age, height, weight, program, calories, target_weight, target_adherence = row
        self.current_client = name
        self.name.set(name)
        self.age.set(age or 0)
        self.height.set(height or 0.0)
        self.weight.set(weight or 0.0)
        self.program.set(program or "")
        self.target_weight.set(target_weight or 0.0)
        self.target_adherence.set(target_adherence or 0)
        self.client_list.set(name)
        self.refresh_summary()
        self.set_status(f"Loaded client: {name}")

    def refresh_summary(self):
        if not self.current_client:
            return
        self.cur.execute("SELECT * FROM clients WHERE name=?", (self.current_client,))
        client = self.cur.fetchone()
        if not client:
            return
        _, name, age, height, weight, program, calories, target_weight, target_adherence = client
        self.cur.execute("SELECT COUNT(*), AVG(adherence) FROM progress WHERE client_name=?", (name,))
        total_weeks, avg_adherence = self.cur.fetchone()
        avg_adherence = round(avg_adherence, 1) if avg_adherence else 0
        self.cur.execute("SELECT date, weight, waist, bodyfat FROM metrics WHERE client_name=? ORDER BY date DESC LIMIT 1", (name,))
        last_metric = self.cur.fetchone()
        last_metric_str = f"{last_metric[0]} | {last_metric[1]}kg, Waist {last_metric[2]}cm, BF {last_metric[3]}%" if last_metric else "None"
        prog_desc = self.programs.get(program, {}).get("desc", "")
        lines = [
            "CLIENT PROFILE", "--------------",
            f"Name      : {name}", f"Age       : {age or '-'}", f"Height    : {height or '-'} cm",
            f"Weight    : {weight or '-'} kg", f"Program   : {program}", f"Calories  : {calories or '-'} kcal/day",
            "", "PROGRAM NOTES", "-------------", prog_desc,
            "", "GOALS", "-----",
            f"Target Weight: {target_weight or '-'} kg | Target Adherence: {target_adherence or '-'}%",
            "", "PROGRESS SUMMARY", "----------------",
            f"Weeks logged: {total_weeks} | Avg adherence: {avg_adherence}%",
            "", "LAST BODY METRICS", "-----------------", last_metric_str,
        ]
        self.summary.configure(state="normal")
        self.summary.delete("1.0", "end")
        self.summary.insert("end", "\n".join(lines))
        self.summary.configure(state="disabled")

    def save_progress(self):
        if not self.name.get().strip():
            messagebox.showwarning("No Client", "Enter client name first")
            return
        week = datetime.now().strftime("Week %U - %Y")
        self.cur.execute("INSERT INTO progress (client_name, week, adherence) VALUES (?, ?, ?)",
                         (self.name.get().strip(), week, int(self.adherence.get())))
        self.conn.commit()
        self.current_client = self.name.get().strip()
        self.refresh_summary()
        messagebox.showinfo("Progress Saved", "Weekly progress logged")

    def ensure_client(self):
        name = self.current_client or self.name.get().strip() or self.client_list.get()
        if not name:
            messagebox.showwarning("No Client", "Select or enter client first")
            return False
        self.current_client = name
        return True

    def show_progress_chart(self):
        if not self.ensure_client():
            return
        self.cur.execute("SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (self.current_client,))
        data = self.cur.fetchall()
        if not data:
            messagebox.showinfo("No Data", "No progress data available")
            return
        plt.figure(figsize=(8, 4))
        plt.plot([r[0] for r in data], [r[1] for r in data], marker="o", linewidth=2)
        plt.title(f"Weekly Adherence - {self.current_client}")
        plt.xlabel("Week"); plt.ylabel("Adherence (%)"); plt.ylim(0, 100); plt.grid(True)
        plt.xticks(rotation=45); plt.tight_layout(); plt.show()

    def show_weight_chart(self):
        if not self.ensure_client():
            return
        self.cur.execute("SELECT date, weight FROM metrics WHERE client_name=? AND weight IS NOT NULL ORDER BY date", (self.current_client,))
        data = self.cur.fetchall()
        if not data:
            messagebox.showinfo("No Data", "No weight metrics available")
            return
        plt.figure(figsize=(8, 4))
        plt.plot([r[0] for r in data], [r[1] for r in data], marker="o", linewidth=2, color="orange")
        plt.title(f"Weight Trend - {self.current_client}")
        plt.xlabel("Date"); plt.ylabel("Weight (kg)"); plt.grid(True)
        plt.xticks(rotation=45); plt.tight_layout(); plt.show()

    def show_bmi_info(self):
        if not self.ensure_client():
            return
        h, w = self.height.get(), self.weight.get()
        if h <= 0 or w <= 0:
            messagebox.showwarning("Missing Data", "Enter valid height and weight first")
            return
        bmi = round(w / (h / 100) ** 2, 1)
        cat = "Underweight" if bmi < 18.5 else "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obese"
        messagebox.showinfo("BMI Info", f"BMI for {self.current_client}: {bmi} ({cat})")

    def open_log_workout_window(self):
        if not self.ensure_client():
            return
        win = tk.Toplevel(self.root)
        win.title(f"Log Workout - {self.current_client}")
        win.configure(bg="#1a1a1a"); win.geometry("450x400")
        tk.Label(win, text="Date (YYYY-MM-DD)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        date_var = tk.StringVar(value=date.today().isoformat())
        tk.Entry(win, textvariable=date_var, bg="#333", fg="white").pack()
        tk.Label(win, text="Workout Type", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        type_var = tk.StringVar()
        ttk.Combobox(win, textvariable=type_var, values=["Strength", "Hypertrophy", "Conditioning", "Mixed", "Mobility"], state="readonly").pack()
        tk.Label(win, text="Duration (min)", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        dur_var = tk.IntVar(value=60)
        tk.Entry(win, textvariable=dur_var, bg="#333", fg="white").pack()
        tk.Label(win, text="Notes", bg="#1a1a1a", fg="white").pack(pady=(10, 0))
        notes_text = tk.Text(win, height=4, bg="#333", fg="white")
        notes_text.pack(fill="x", padx=10)
        def save_workout():
            w_date, w_type = date_var.get().strip(), type_var.get().strip()
            if not w_date or not w_type:
                messagebox.showerror("Error", "Date and type required"); return
            self.cur.execute("INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?, ?, ?, ?, ?)",
                             (self.current_client, w_date, w_type, int(dur_var.get()), notes_text.get("1.0", "end").strip()))
            self.conn.commit()
            messagebox.showinfo("Saved", "Workout logged"); win.destroy()
        ttk.Button(win, text="Save Workout", command=save_workout).pack(pady=15)

    def open_log_metrics_window(self):
        if not self.ensure_client():
            return
        win = tk.Toplevel(self.root)
        win.title(f"Log Body Metrics - {self.current_client}")
        win.configure(bg="#1a1a1a"); win.geometry("350x300")
        fields = [("Date (YYYY-MM-DD)", tk.StringVar(value=date.today().isoformat())),
                  ("Weight (kg)", tk.DoubleVar(value=self.weight.get())),
                  ("Waist (cm)", tk.DoubleVar()), ("Bodyfat (%)", tk.DoubleVar())]
        for label, var in fields:
            tk.Label(win, text=label, bg="#1a1a1a", fg="white").pack(pady=(10, 0))
            tk.Entry(win, textvariable=var, bg="#333", fg="white").pack()
        def save_metrics():
            m_date = fields[0][1].get().strip()
            if not m_date:
                messagebox.showerror("Error", "Date required"); return
            self.cur.execute("INSERT INTO metrics (client_name, date, weight, waist, bodyfat) VALUES (?, ?, ?, ?, ?)",
                             (self.current_client, m_date, fields[1][1].get(), fields[2][1].get(), fields[3][1].get()))
            self.conn.commit()
            self.refresh_summary()
            messagebox.showinfo("Saved", "Metrics logged"); win.destroy()
        ttk.Button(win, text="Save Metrics", command=save_metrics).pack(pady=15)

    def open_workout_history_window(self):
        if not self.ensure_client():
            return
        win = tk.Toplevel(self.root)
        win.title(f"Workout History - {self.current_client}"); win.geometry("700x400")
        columns = ("date", "type", "duration", "notes")
        tree = ttk.Treeview(win, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col.title())
        tree.pack(fill="both", expand=True)
        self.cur.execute("SELECT date, workout_type, duration_min, notes FROM workouts WHERE client_name=? ORDER BY date DESC", (self.current_client,))
        for row in self.cur.fetchall():
            tree.insert("", "end", values=row)


if __name__ == "__main__":
    root = tk.Tk()
    app = ACEestApp(root)
    root.mainloop()
