from flask import Flask, render_template
from flask_login import current_user

from config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.recommendation import recommendation_bp
    from app.routes.product import product_bp
    from app.routes.calendar import calendar_bp
    from app.routes.purchase import purchase_bp
    from app.routes.cart import cart_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(purchase_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_globals():
        unread_count = 0
        cart_count = 0
        if current_user.is_authenticated:
            from app.models import Notification, Cart

            unread_count = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
            cart = Cart.query.filter_by(user_id=current_user.id).first()
            cart_count = cart.total_quantity if cart else 0

        return {
            "service_name": app.config["SERVICE_NAME"],
            "service_tagline": app.config["SERVICE_TAGLINE"],
            "unread_notification_count": unread_count,
            "cart_item_count": cart_count,
        }

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    if app.config.get("AUTO_SEED_IF_EMPTY", True):
        with app.app_context():
            _run_startup_migrations()
            db.create_all()
            _ensure_additive_columns()

            from app.models import Product

            if Product.query.count() == 0:
                from seed import build_demo_data

                build_demo_data()

    return app


def _run_startup_migrations():
    """One-off cleanup for a database that previously belonged to an
    unrelated app (see README) - runs before create_all()."""
    from sqlalchemy import inspect as sa_inspect, text

    insp = sa_inspect(db.engine)
    if "users" in insp.get_table_names():
        existing_columns = {c["name"] for c in insp.get_columns("users")}
        if "email" not in existing_columns:
            # A `users` table exists but doesn't match our schema - it's
            # left over from an unrelated app that previously used this
            # database. Drop it (and its dependents) so create_all() can
            # lay down our own schema.
            with db.engine.begin() as conn:
                conn.execute(text("DROP TABLE IF EXISTS tasks"))
                conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))


def _ensure_additive_columns():
    """create_all() only creates missing tables, never alters existing
    ones. Purely-additive model changes (a new nullable column) are applied
    here instead of pulling in a full migration framework for an MVP."""
    from sqlalchemy import inspect as sa_inspect, text

    insp = sa_inspect(db.engine)
    additive_columns = {
        "calendar_events": [("keywords", "VARCHAR(255)")],
    }
    for table, columns in additive_columns.items():
        if table not in insp.get_table_names():
            continue
        existing = {c["name"] for c in insp.get_columns(table)}
        for name, ddl_type in columns:
            if name not in existing:
                with db.engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}"))
