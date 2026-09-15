import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
# Vercel's serverless filesystem is read-only except /tmp, and /tmp is not
# shared or persistent across invocations - data added there can disappear
# on the next cold start.
DATABASE = Path("/tmp/todo.db") if os.environ.get("VERCEL") else BASE_DIR / "todo.db"

app = Flask(__name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        db.commit()


@app.route("/")
def index():
    filter_ = request.args.get("filter", "all")
    db = get_db()
    if filter_ == "active":
        tasks = db.execute(
            "SELECT * FROM tasks WHERE done = 0 ORDER BY id DESC"
        ).fetchall()
    elif filter_ == "done":
        tasks = db.execute(
            "SELECT * FROM tasks WHERE done = 1 ORDER BY id DESC"
        ).fetchall()
    else:
        tasks = db.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()

    total = db.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()["c"]
    done_count = db.execute(
        "SELECT COUNT(*) AS c FROM tasks WHERE done = 1"
    ).fetchone()["c"]

    return render_template(
        "index.html",
        tasks=tasks,
        filter=filter_,
        total=total,
        done_count=done_count,
    )


@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    if title:
        db = get_db()
        db.execute(
            "INSERT INTO tasks (title, done, created_at) VALUES (?, 0, ?)",
            (title, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle(task_id):
    db = get_db()
    db.execute(
        "UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,)
    )
    db.commit()
    return redirect(request.referrer or url_for("index"))


@app.route("/edit/<int:task_id>", methods=["POST"])
def edit(task_id):
    title = request.form.get("title", "").strip()
    if title:
        db = get_db()
        db.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
        db.commit()
    return redirect(request.referrer or url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return redirect(request.referrer or url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
