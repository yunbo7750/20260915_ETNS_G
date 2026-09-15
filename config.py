import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalize_database_url(url: str) -> str:
    """SQLAlchemy 1.4+ requires the 'postgresql://' scheme, but many hosts
    (Supabase, Heroku, ...) hand out 'postgres://' connection strings."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


class Config:
    """Central configuration. All tunable business rules live here so the
    recommendation engines never hardcode numbers in their logic."""

    # --- Service identity (kept out of templates/code so it can be renamed) ---
    SERVICE_NAME = os.environ.get("SERVICE_NAME", "ETNERS LIFE")
    SERVICE_TAGLINE = os.environ.get(
        "SERVICE_TAGLINE", "찾아서 사는 쇼핑몰에서, 필요할 때 먼저 알려주는 쇼핑몰로."
    )

    # --- Core Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "etners_life.db")
    ))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"pool_pre_ping": True} if not SQLALCHEMY_DATABASE_URI.startswith("sqlite") else {}
    )

    # --- Timezone ---
    # Default service timezone. Per-user timezone support (based on User.country)
    # can be layered on top of this later without changing callers.
    DEFAULT_TIMEZONE = os.environ.get("DEFAULT_TIMEZONE", "Asia/Seoul")

    # --- Recommendation engine: REORDER ---
    # A product must have at least this many past purchases before a purchase
    # cycle (average interval) can be computed for it.
    REORDER_MIN_PURCHASE_COUNT = 2
    # How many days before the predicted next-purchase date we start recommending.
    REORDER_LEAD_DAYS = int(os.environ.get("REORDER_LEAD_DAYS", 7))

    # --- Recommendation engine: LIFE CALENDAR ---
    # Days-before-event checkpoints at which a life-event recommendation fires.
    EVENT_RECOMMENDATION_DAYS = [30, 14, 7, 3]
    # Maps an event_type to the product categories/tags considered relevant.
    EVENT_TYPE_PRODUCT_TAGS = {
        "생일": ["어린이도서", "간식", "선물", "파티용품"],
        "자녀생일": ["어린이도서", "간식", "선물", "파티용품"],
        "결혼기념일": ["선물", "와인", "간식"],
        "학교행사": ["어린이도서", "간식", "문구"],
        "한국방문": ["생활용품", "선물", "도서"],
        "해외출국": ["생활용품", "비상식품"],
        "이사": ["생활용품", "세제", "욕실용품"],
        "명절": ["명절선물", "식품", "간편식"],
        "설날": ["명절선물", "식품", "간편식"],
        "추석": ["명절선물", "식품", "간편식"],
        "크리스마스": ["선물", "간식", "파티용품"],
        "기타": ["생활용품"],
    }

    # --- Recommendation engine: PERSONAL LIFE ---
    CHILD_PRODUCT_CATEGORIES = ["어린이도서", "간식", "장난감"]

    # --- Scoring weights (must sum conceptually to ~100 for a "perfect" match) ---
    SCORE_REORDER = 40
    SCORE_LIFE_EVENT = 30
    SCORE_PERSONAL = 20
    SCORE_RECENT_PURCHASE = 10
    SCORE_MAX = 100

    # --- Recommendation display limits ---
    HOME_MAX_RECOMMENDATIONS = int(os.environ.get("HOME_MAX_RECOMMENDATIONS", 6))
    PAGE_MAX_RECOMMENDATIONS = int(os.environ.get("PAGE_MAX_RECOMMENDATIONS", 20))

    # How long a generated recommendation batch stays "fresh" before the engine
    # regenerates it for a user (avoids recomputing on every single page view).
    RECOMMENDATION_REFRESH_HOURS = int(os.environ.get("RECOMMENDATION_REFRESH_HOURS", 12))

    # If true, the app factory auto-creates tables and (if the Product table
    # is empty) populates demo data on startup. This lets a freshly
    # provisioned, empty production database (e.g. Supabase/Postgres behind
    # a serverless Vercel deployment) bootstrap itself without a separate
    # migration step.
    AUTO_SEED_IF_EMPTY = os.environ.get("AUTO_SEED_IF_EMPTY", "true").lower() == "true"


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    AUTO_SEED_IF_EMPTY = False
