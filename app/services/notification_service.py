from app.extensions import db
from app.models import Notification
from app.models.recommendation import TYPE_REORDER, TYPE_LIFE_EVENT


def create_notification(user, type_, title, message, reference_type=None, reference_id=None):
    notification = Notification(
        user_id=user.id,
        type=type_,
        title=title,
        message=message,
        reference_type=reference_type,
        reference_id=reference_id,
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def notify_new_recommendations(user, recommendations):
    """One summary notification per new recommendation batch, worded
    according to the strongest signal in it (reorder vs. life event)."""
    if not recommendations:
        return None

    reorder_count = sum(1 for r in recommendations if r.type == TYPE_REORDER)
    life_event_recs = [r for r in recommendations if r.type == TYPE_LIFE_EVENT]

    if life_event_recs:
        rec = life_event_recs[0]
        title = "다가오는 일정 알림"
        message = rec.reason
        reference_id = rec.id
    elif reorder_count > 0:
        title = "다시 구매할 시기가 된 상품이 있어요"
        sample = next(r for r in recommendations if r.type == TYPE_REORDER)
        others = reorder_count - 1
        message = f"{sample.product.name}" + (f" 외 {others}개" if others > 0 else "") + " 상품을 확인해보세요."
        reference_id = sample.id
    else:
        title = "새로운 추천이 도착했어요"
        others = len(recommendations) - 1
        message = recommendations[0].product.name + (f" 외 {others}개" if others > 0 else "") + " 추천 상품을 확인해보세요."
        reference_id = recommendations[0].id

    return create_notification(
        user,
        type_="RECOMMENDATION",
        title=title,
        message=message,
        reference_type="recommendation",
        reference_id=reference_id,
    )
