import os

import psycopg2
import psycopg2.extras
from flask import Flask, g, redirect, render_template, request, url_for

DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = psycopg2.connect(DATABASE_URL, sslmode="require")
    return db


def query(sql, params=(), fetch=None):
    db = get_db()
    with db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        result = cur.fetchall() if fetch == "all" else cur.fetchone() if fetch == "one" else None
    db.commit()
    return result


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


SELECT_TASKS = """
    SELECT id, title, done,
           to_char(created_at AT TIME ZONE 'Asia/Seoul', 'YYYY-MM-DD HH24:MI') AS created_at
    FROM tasks
    {where}
    ORDER BY id DESC
"""


@app.route("/")
def index():
    filter_ = request.args.get("filter", "all")
    where = {"active": "WHERE NOT done", "done": "WHERE done"}.get(filter_, "")
    tasks = query(SELECT_TASKS.format(where=where), fetch="all")

    counts = query(
        "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE done) AS done_count FROM tasks",
        fetch="one",
    )

    return render_template(
        "index.html",
        tasks=tasks,
        filter=filter_,
        total=counts["total"],
        done_count=counts["done_count"],
    )


@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    if title:
        query("INSERT INTO tasks (title) VALUES (%s)", (title,))
    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle(task_id):
    query("UPDATE tasks SET done = NOT done WHERE id = %s", (task_id,))
    return redirect(request.referrer or url_for("index"))


@app.route("/edit/<int:task_id>", methods=["POST"])
def edit(task_id):
    title = request.form.get("title", "").strip()
    if title:
        query("UPDATE tasks SET title = %s WHERE id = %s", (title, task_id))
    return redirect(request.referrer or url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    query("DELETE FROM tasks WHERE id = %s", (task_id,))
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
