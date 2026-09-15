"""Seed script - populates the database with demo data so the service can be
explored immediately after `flask init-db`.

Run with:  python seed.py
Re-running this script wipes and recreates all tables.

`build_demo_data()` is also imported and called automatically by the app
factory (see app/__init__.py) whenever it finds an empty, freshly
provisioned database (e.g. a brand new Supabase/Postgres instance behind a
Vercel deployment) - it never drops or creates tables itself, so it's safe
to call from a running app.
"""
from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import (
    User, FamilyMember, Preference, Product, PurchaseHistory,
    CalendarEvent, Recommendation, Notification, Cart, CartItem,
)

TODAY = date.today()

PRODUCTS = [
    # (name, category, price, unit, tags, season, target_age, description)
    ("신라면", "식품", 4000, "5개입", "라면,매운맛", "전체", "전연령", "한국인의 소울푸드, 얼큰한 라면."),
    ("진라면 매운맛", "식품", 4200, "5개입", "라면,매운맛", "전체", "전연령", "깔끔한 매운맛의 진라면."),
    ("포기김치 1kg", "식품", 15000, "1kg", "김치,반찬", "전체", "전연령", "잘 익은 포기김치."),
    ("즉석밥(햇반)", "간편식", 6000, "12개입", "즉석밥,간편식", "전체", "전연령", "3분이면 완성되는 즉석밥."),
    ("참치캔", "식품", 8000, "5개입", "참치,비상식품", "전체", "전연령", "밥반찬으로 좋은 참치캔."),
    ("컵라면 모음", "간편식", 10000, "6개입", "라면,비상식품", "전체", "전연령", "다양한 맛의 컵라면 모음."),
    ("짜장라면", "식품", 4500, "4개입", "라면", "전체", "전연령", "달콤짭짤한 짜장라면."),
    ("떡볶이 밀키트", "간편식", 7000, "2인분", "간편식,매운맛", "전체", "전연령", "간편하게 즐기는 떡볶이."),
    ("냉동만두", "간편식", 9000, "1kg", "간편식", "전체", "전연령", "촉촉한 냉동 만두."),
    ("미역국 밀키트", "간편식", 6000, "2인분", "간편식,미역국", "전체", "전연령", "생일에 어울리는 미역국."),
    ("새우깡", "과자", 2000, "90g", "과자,간식", "전체", "전연령", "국민 과자 새우깡."),
    ("초코파이", "과자", 5000, "12개입", "과자,간식,선물", "전체", "전연령", "부드러운 초코파이."),
    ("허니버터칩", "과자", 3000, "60g", "과자,간식", "전체", "전연령", "달콤한 허니버터칩."),
    ("어린이 비타민 젤리", "과자", 8000, "60정", "간식,어린이도서,건강,비타민", "전체", "3-10세", "아이들이 좋아하는 비타민 젤리."),
    ("뻥튀기", "과자", 2500, "200g", "과자,간식", "전체", "전연령", "가볍게 즐기는 뻥튀기."),
    ("식혜", "음료", 5000, "500ml x4", "음료,명절선물", "가을", "전연령", "달콤한 전통 식혜."),
    ("수정과", "음료", 5500, "500ml x4", "음료,명절선물", "겨울", "전연령", "향긋한 수정과."),
    ("원두커피 드립백", "커피", 12000, "20개입", "커피", "전체", "성인", "향긋한 드립백 커피."),
    ("인스턴트 커피믹스", "커피", 9000, "100개입", "커피", "전체", "성인", "간편한 커피믹스."),
    ("콜드브루 커피", "커피", 15000, "4개입", "커피,선물", "여름", "성인", "진한 콜드브루 커피."),
    ("섬유유연제", "생활용품", 8000, "2L", "생활용품,세제", "전체", "전연령", "은은한 향의 섬유유연제."),
    ("세탁세제", "세제", 9500, "3kg", "세제,생활용품", "전체", "전연령", "강력한 세척력의 세탁세제."),
    ("주방세제", "세제", 4000, "500ml", "세제,생활용품", "전체", "전연령", "기름때에 강한 주방세제."),
    ("샴푸", "욕실용품", 7000, "500ml", "욕실용품,생활용품", "전체", "전연령", "두피 자극을 줄여주는 샴푸."),
    ("바디워시", "욕실용품", 7500, "500ml", "욕실용품,생활용품", "전체", "전연령", "촉촉한 바디워시."),
    ("치약 세트", "욕실용품", 6000, "3개입", "욕실용품,생활용품", "전체", "전연령", "산뜻한 치약 세트."),
    ("어린이 동화책 전집", "어린이도서", 45000, "10권", "어린이도서,도서,선물", "전체", "3-8세", "감성을 키워주는 동화책 전집."),
    ("어린이 학습만화", "어린이도서", 12000, "1권", "어린이도서,도서", "전체", "7-12세", "재미있게 배우는 학습만화."),
    ("베스트셀러 소설", "도서", 15000, "1권", "도서", "전체", "성인", "화제의 베스트셀러 소설."),
    ("자기계발서", "도서", 16000, "1권", "도서", "전체", "성인", "동기부여가 되는 자기계발서."),
    ("파티용 풍선 세트", "기타", 8000, "1세트", "파티용품,선물", "전체", "전연령", "생일 파티 필수템."),
    ("생일 케이크 세트", "기타", 18000, "1세트", "선물,파티용품", "전체", "전연령", "홈베이킹 생일 케이크 세트."),
    ("문구 세트", "기타", 7000, "1세트", "문구", "전체", "전연령", "연필과 노트가 포함된 문구 세트."),
    ("와인(선물용)", "기타", 35000, "750ml", "와인,선물", "전체", "성인", "특별한 날을 위한 와인."),
    ("여행용 세면도구 파우치", "생활용품", 12000, "1세트", "생활용품,비상식품", "전체", "전연령", "출국 전 챙기기 좋은 파우치."),
    ("상비약 세트", "생활용품", 20000, "1세트", "생활용품,비상식품,건강", "전체", "전연령", "해외 생활 필수 상비약 세트."),
    ("명절 선물세트(한과)", "기타", 30000, "1세트", "명절선물,선물", "전체", "전연령", "정성이 담긴 한과 선물세트."),
    ("축구공 세트", "기타", 15000, "1세트", "장난감,축구,선물", "전체", "5-12세", "아이와 함께 즐기는 축구공 세트."),
]

# Product image: every product shows a category-themed illustration
# (app/static/images/products/) rather than a generic placeholder icon.
CATEGORY_IMAGE_SLUG = {
    "식품": "food",
    "간편식": "instant",
    "과자": "snack",
    "음료": "drink",
    "커피": "coffee",
    "생활용품": "household",
    "세제": "detergent",
    "욕실용품": "bath",
    "도서": "book",
    "어린이도서": "kids-book",
    "기타": "etc",
}


def _product_image_url(category: str) -> str:
    slug = CATEGORY_IMAGE_SLUG.get(category, "etc")
    return f"/static/images/products/{slug}.svg"


def gen_dates(last_ago_days, interval_days, count):
    """count purchase dates, most recent `last_ago_days` days ago, spaced
    `interval_days` apart going backwards. Returned oldest-first."""
    last_date = TODAY - timedelta(days=last_ago_days)
    dates = [last_date - timedelta(days=interval_days * i) for i in range(count)]
    return list(reversed(dates))


def add_purchases(user, product_map, product_name, last_ago_days, interval_days, count, qty=1):
    product = product_map[product_name]
    for d in gen_dates(last_ago_days, interval_days, count):
        db.session.add(
            PurchaseHistory(
                user_id=user.id,
                product_id=product.id,
                quantity=qty,
                purchased_at=d,
                price=product.price,
            )
        )


def add_event(user, title, event_type, days_from_today, description=None, keywords=None):
    db.session.add(
        CalendarEvent(
            user_id=user.id,
            title=title,
            event_type=event_type,
            event_date=TODAY + timedelta(days=days_from_today),
            description=description,
            keywords=keywords,
        )
    )


def add_preference(user, target_type, sentiment="like", category=None, product=None):
    db.session.add(
        Preference(
            user_id=user.id,
            target_type=target_type,
            sentiment=sentiment,
            category=category,
            product_id=product.id if product else None,
        )
    )


def create_user(username, password, name, role="user", country=None, city=None,
                 assignment_start_days_ago=None, assignment_end_days_from_now=None):
    user = User(
        username=username,
        email=f"{username}@etners-life.example",
        name=name,
        role=role,
        country=country,
        city=city,
        onboarding_completed=(role == "user"),
        assignment_start_date=(TODAY - timedelta(days=assignment_start_days_ago))
        if assignment_start_days_ago else None,
        assignment_end_date=(TODAY + timedelta(days=assignment_end_days_from_now))
        if assignment_end_days_from_now else None,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    db.session.add(Cart(user_id=user.id))
    return user


def build_demo_data():
    """Populates products, demo users, and their purchase/calendar/preference
    data. Assumes tables already exist and are empty - does NOT drop or
    create tables itself, so it's safe to call from a running app (e.g. to
    auto-seed a freshly provisioned, empty production database)."""
    print("Creating products...")
    product_map = {}
    for name, category, price, unit, tags, season, target_age, desc in PRODUCTS:
        product = Product(
            name=name, category=category, price=price, unit=unit,
            tags=tags, season=season, target_age=target_age, description=desc,
            image_url=_product_image_url(category),
            stock=200, active=True,
        )
        db.session.add(product)
        product_map[name] = product
    db.session.flush()

    print("Creating admin account...")
    create_user("admin", "admin1234", "관리자", role="admin")

    print("Creating user accounts and demo data...")

    # --- user01: 김민정 - 미국 뉴저지, 배우자+자녀2, 커피/식품 선호 ---
    u1 = create_user(
        "user01", "user1234", "김민정",
        country="미국", city="뉴저지",
        assignment_start_days_ago=400, assignment_end_days_from_now=300,
    )
    db.session.add(FamilyMember(user_id=u1.id, relation="배우자", name="이한결"))
    db.session.add(FamilyMember(
        user_id=u1.id, relation="자녀", name="이도윤",
        birth_date=date(TODAY.year - 8, 3, 15), interests="도서,과자",
    ))
    db.session.add(FamilyMember(
        user_id=u1.id, relation="자녀", name="이서준",
        birth_date=date(TODAY.year - 5, 11, 2), interests="장난감,간식",
    ))
    db.session.flush()
    add_preference(u1, "category", category="식품")
    add_preference(u1, "category", category="커피")
    add_preference(u1, "product", product=product_map["신라면"])
    add_purchases(u1, product_map, "신라면", last_ago_days=42, interval_days=45, count=5, qty=2)
    add_purchases(u1, product_map, "즉석밥(햇반)", last_ago_days=25, interval_days=30, count=6, qty=1)
    add_purchases(u1, product_map, "원두커피 드립백", last_ago_days=55, interval_days=60, count=4, qty=1)
    add_purchases(u1, product_map, "어린이 동화책 전집", last_ago_days=80, interval_days=90, count=3, qty=1)
    add_event(
        u1, "이도윤 생일", "자녀생일", 14,
        keywords="축구 좋아함, 비타민 필요",
    )
    add_event(u1, "한국 방문", "한국방문", 30)

    # --- user02: 이서연 - 독일, 1인 가구, 도서/생활용품 선호, 도서 다독 ---
    u2 = create_user(
        "user02", "user1234", "이서연",
        country="독일", city="뮌헨",
        assignment_start_days_ago=200, assignment_end_days_from_now=500,
    )
    add_preference(u2, "category", category="도서")
    add_preference(u2, "category", category="생활용품")
    add_purchases(u2, product_map, "베스트셀러 소설", last_ago_days=10, interval_days=20, count=8, qty=1)
    add_purchases(u2, product_map, "샴푸", last_ago_days=38, interval_days=40, count=5, qty=1)
    add_purchases(u2, product_map, "세탁세제", last_ago_days=58, interval_days=60, count=4, qty=1)
    add_event(u2, "숙소 이사", "이사", 7)
    add_event(u2, "크리스마스", "크리스마스", 100)

    # --- user03: 박준호 - 싱가포르, 배우자, 커피/과자 선호 ---
    u3 = create_user(
        "user03", "user1234", "박준호",
        country="싱가포르", city="싱가포르",
        assignment_start_days_ago=600, assignment_end_days_from_now=120,
    )
    db.session.add(FamilyMember(user_id=u3.id, relation="배우자", name="박서현"))
    db.session.flush()
    add_preference(u3, "category", category="커피")
    add_preference(u3, "category", category="과자")
    add_purchases(u3, product_map, "인스턴트 커피믹스", last_ago_days=33, interval_days=35, count=6, qty=1)
    add_purchases(u3, product_map, "새우깡", last_ago_days=5, interval_days=15, count=6, qty=2)
    add_purchases(u3, product_map, "초코파이", last_ago_days=45, interval_days=50, count=4, qty=1)
    add_event(u3, "결혼기념일", "결혼기념일", 3)

    # --- user04: 최지훈 - 베트남, 자녀 1명(10세), 와인 비선호 ---
    u4 = create_user(
        "user04", "user1234", "최지훈",
        country="베트남", city="호치민",
        assignment_start_days_ago=150, assignment_end_days_from_now=400,
    )
    db.session.add(FamilyMember(
        user_id=u4.id, relation="자녀", name="최하은",
        birth_date=date(TODAY.year - 10, 6, 20), interests="학습만화,어린이도서",
    ))
    db.session.flush()
    add_preference(u4, "product", sentiment="dislike", product=product_map["와인(선물용)"])
    add_purchases(u4, product_map, "어린이 학습만화", last_ago_days=58, interval_days=60, count=4, qty=1)
    add_purchases(u4, product_map, "참치캔", last_ago_days=20, interval_days=25, count=6, qty=2)
    add_purchases(u4, product_map, "상비약 세트", last_ago_days=100, interval_days=120, count=2, qty=1)
    add_event(u4, "학교 행사", "학교행사", 3, keywords="건강 챙기기")
    add_event(u4, "일시 출국", "해외출국", 20)

    # --- user05: 정수빈 - 아랍에미리트, 1인 가구, 데이터가 적은 신규 유저 ---
    u5 = create_user(
        "user05", "user1234", "정수빈",
        country="아랍에미리트", city="두바이",
        assignment_start_days_ago=30, assignment_end_days_from_now=700,
    )
    add_purchases(u5, product_map, "즉석밥(햇반)", last_ago_days=28, interval_days=30, count=3, qty=1)

    db.session.commit()

    print("Generating initial recommendation batches for demo users...")
    from app.services import recommendation_engine

    for user in [u1, u2, u3, u4, u5]:
        recommendation_engine.generate_for_user(user)

    print("Seed complete.")
    print(f" - Products: {Product.query.count()}")
    print(f" - Users: {User.query.count()}")
    print(f" - Purchases: {PurchaseHistory.query.count()}")
    print(f" - Calendar events: {CalendarEvent.query.count()}")
    print(f" - Recommendations generated: {Recommendation.query.count()}")
    print(f" - Notifications: {Notification.query.count()}")


def run():
    """CLI entry point for local development: wipes and recreates all
    tables, then populates them with fresh demo data."""
    app = create_app()
    with app.app_context():
        print("Dropping and recreating all tables...")
        db.drop_all()
        db.create_all()
        build_demo_data()


if __name__ == "__main__":
    run()
