import os
from functools import wraps

import psycopg2
import psycopg2.extras
from flask import Flask, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]


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


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        return render_template("register.html", error="아이디와 비밀번호를 입력해주세요.")

    existing = query("SELECT id FROM users WHERE username = %s", (username,), fetch="one")
    if existing:
        return render_template("register.html", error="이미 사용 중인 아이디입니다.")

    user = query(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
        (username, generate_password_hash(password)),
        fetch="one",
    )
    session["user_id"] = user["id"]
    session["username"] = username
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = query("SELECT * FROM users WHERE username = %s", (username,), fetch="one")
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="아이디 또는 비밀번호가 올바르지 않습니다.")

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


SELECT_TASKS = """
    SELECT id, title, done,
           to_char(created_at AT TIME ZONE 'Asia/Seoul', 'YYYY-MM-DD HH24:MI') AS created_at
    FROM tasks
    WHERE user_id = %s {extra}
    ORDER BY id DESC
"""


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    filter_ = request.args.get("filter", "all")
    extra = {"active": "AND NOT done", "done": "AND done"}.get(filter_, "")
    tasks = query(SELECT_TASKS.format(extra=extra), (user_id,), fetch="all")

    counts = query(
        "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE done) AS done_count FROM tasks WHERE user_id = %s",
        (user_id,),
        fetch="one",
    )

    return render_template(
        "index.html",
        tasks=tasks,
        filter=filter_,
        total=counts["total"],
        done_count=counts["done_count"],
        username=session["username"],
    )


@app.route("/add", methods=["POST"])
@login_required
def add():
    title = request.form.get("title", "").strip()
    if title:
        query("INSERT INTO tasks (title, user_id) VALUES (%s, %s)", (title, session["user_id"]))
    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>", methods=["POST"])
@login_required
def toggle(task_id):
    query(
        "UPDATE tasks SET done = NOT done WHERE id = %s AND user_id = %s",
        (task_id, session["user_id"]),
    )
    return redirect(request.referrer or url_for("index"))


@app.route("/edit/<int:task_id>", methods=["POST"])
@login_required
def edit(task_id):
    title = request.form.get("title", "").strip()
    if title:
        query(
            "UPDATE tasks SET title = %s WHERE id = %s AND user_id = %s",
            (title, task_id, session["user_id"]),
        )
    return redirect(request.referrer or url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete(task_id):
    query(
        "DELETE FROM tasks WHERE id = %s AND user_id = %s",
        (task_id, session["user_id"]),
    )
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
