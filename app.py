from app import create_app
from app.extensions import db

app = create_app()


@app.cli.command("init-db")
def init_db():
    """Creates all database tables (run once before first use)."""
    with app.app_context():
        db.create_all()
        print("Database tables created.")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
