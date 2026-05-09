from datetime import date

from django.db.models import Avg, Count


DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_SHORT = {"monday": "Mon", "tuesday": "Tue", "wednesday": "Wed",
             "thursday": "Thu", "friday": "Fri", "saturday": "Sat", "sunday": "Sun"}

STATUS_CLASS = {
    "pending": "pending",
    "confirmed": "confirmed",
    "completed": "completed",
    "cancelled": "cancelled",
}


def initials(user):
    fn = (user.firstName or user.first_name or "").strip()
    ln = (user.lastName or user.last_name or "").strip()
    return ((fn[:1] or "?") + (ln[:1] or "")).upper()


def first_name(user):
    return (user.firstName or user.first_name or "").strip()


def last_name(user):
    return (user.lastName or user.last_name or "").strip()


def last_name_initial(user):
    return (last_name(user)[:1] or "").upper()


def stars(rating):
    n = int(round(rating or 0))
    n = max(0, min(5, n))
    return {"stars_full": range(n), "stars_empty": range(5 - n)}


def format_rating(rating):
    if rating is None:
        return "—"
    return f"{float(rating):.1f}"


def tutor_card(tutor):
    user = tutor.userID
    avg = getattr(tutor, "avg_rating", None)
    review_count = getattr(tutor, "review_count", 0) or 0
    subjects_qs = tutor.tutor_subjects.select_related("subjectID").all()
    rates = [ts.ratePerHour for ts in subjects_qs]
    return {
        "tutorId": tutor.tutorId,
        "userID_id": tutor.userID_id,
        "first_name": first_name(user),
        "last_name_initial": last_name_initial(user),
        "initials": initials(user),
        "avg_rating": format_rating(avg),
        "review_count": review_count,
        "is_verified": tutor.isVerified,
        "bio_preview": (tutor.bio or "")[:160],
        "subjects": [ts.subjectID.name for ts in subjects_qs],
        "rate_per_hour": min(rates) if rates else None,
        "distance_miles": "—",
        **stars(avg),
    }


def tutor_profile(tutor):
    user = tutor.userID
    from .models import Review

    reviews_qs = (
        Review.objects
        .filter(bookingID__tutorSubjectID__tutorID=tutor)
        .select_related("bookingID__clientID__userID", "bookingID__tutorSubjectID__subjectID")
        .order_by("-reviewDate")
    )
    agg = reviews_qs.aggregate(avg=Avg("rating"), count=Count("rating"))
    avg = agg["avg"]
    review_count = agg["count"] or 0

    subjects_qs = tutor.tutor_subjects.select_related("subjectID").all()
    rates = [ts.ratePerHour for ts in subjects_qs]

    creds = list(tutor.credentials.order_by("-issueDate"))
    bg = tutor.background_checks.order_by("-dateCompleted").first()
    bg_status = bg.get_status_display() if bg else "Pending"

    avail_qs = tutor.availabilities.order_by("startTime").all()
    by_day = {d: [] for d in DAY_ORDER}
    for slot in avail_qs:
        by_day.setdefault(slot.dayOfWeek, []).append(slot)

    availability = [{
        "short_name": DAY_SHORT.get(d, d.title()),
        "slots": [{
            "availabilityId": s.availabilityId,
            "start_time": s.startTime.strftime("%-I:%M %p") if hasattr(s.startTime, "strftime") and _supports_dash_format() else s.startTime.strftime("%I:%M %p").lstrip("0"),
            "end_time": s.endTime.strftime("%I:%M %p").lstrip("0"),
        } for s in by_day[d]],
    } for d in DAY_ORDER]

    available_slots = [{
        "availability_id": s.availabilityId,
        "day_of_week": s.get_dayOfWeek_display(),
        "start_time": s.startTime.strftime("%I:%M %p").lstrip("0"),
        "end_time": s.endTime.strftime("%I:%M %p").lstrip("0"),
    } for s in avail_qs]

    return {
        "tutorId": tutor.tutorId,
        "userID_id": tutor.userID_id,
        "first_name": first_name(user),
        "last_name_initial": last_name_initial(user),
        "initials": initials(user),
        "avg_rating": format_rating(avg),
        "review_count": review_count,
        "is_verified": tutor.isVerified,
        "background_check_status": bg_status,
        "service_radius_miles": tutor.serviceRadiusMiles,
        "bio": tutor.bio or "",
        "default_rate": min(rates) if rates else 0,
        "subjects": [{
            "tutor_subject_id": ts.TutorSubjectId,
            "subject_name": ts.subjectID.name,
            "skill_level": ts.get_skillLevel_display(),
            "category": ts.subjectID.category,
            "rate_per_hour": ts.ratePerHour,
        } for ts in subjects_qs],
        "available_slots": available_slots,
        "availability": availability,
        "credentials": [{
            "type": c.type,
            "issuing_institution": c.issuingInstitution,
            "issue_date": c.issueDate,
            "document_url": c.documentURL,
        } for c in creds],
        "reviews": [review_row(r) for r in reviews_qs[:20]],
        **stars(avg),
    }


def _supports_dash_format():
    return False  # Windows doesn't support %-I; use plain %I and lstrip


def booking_row(booking, viewer_type):
    sub = booking.tutorSubjectID.subjectID
    tutor_user = booking.tutorSubjectID.tutorID.userID
    client_user = booking.clientID.userID
    has_review = hasattr(booking, "review")
    payment = getattr(booking, "payment", None)
    sched = booking.scheduledDateTime
    return {
        "bookingId": booking.bookingId,
        "month": sched.strftime("%b").upper(),
        "day": sched.strftime("%d").lstrip("0"),
        "time": sched.strftime("%I:%M %p").lstrip("0"),
        "subject_name": sub.name,
        "client_name": f"{first_name(client_user)} {last_name_initial(client_user)}.",
        "tutor_name": f"{first_name(tutor_user)} {last_name_initial(tutor_user)}.",
        "tutor_user_id": tutor_user.userId,
        "client_initial": first_name(client_user)[:1].upper() or "?",
        "tutor_initials": initials(tutor_user),
        "duration_minutes": booking.durationMinutes,
        "amount": payment.amount if payment else "—",
        "location": booking.locationID.city if booking.locationID else "—",
        "scheduled_date": sched.strftime("%b %d, %Y"),
        "status": booking.get_status_display(),
        "status_class": STATUS_CLASS.get(booking.status, "pending"),
        "has_review": has_review,
        "cancelled_date": sched.strftime("%b %d, %Y") if booking.status == "cancelled" else "",
    }


def split_bookings(bookings, viewer_type, now):
    upcoming, pending, past, cancelled = [], [], [], []
    for b in bookings:
        row = booking_row(b, viewer_type)
        if b.status == "cancelled":
            cancelled.append(row)
        elif b.status == "pending":
            pending.append(row)
        elif b.status == "completed" or b.scheduledDateTime < now:
            past.append(row)
        else:
            upcoming.append(row)
    return upcoming, pending, past, cancelled


def review_row(review):
    booking = review.bookingID
    client_user = booking.clientID.userID
    sub = booking.tutorSubjectID.subjectID
    return {
        "client_name": f"{first_name(client_user)} {last_name_initial(client_user)}.",
        "client_initial": first_name(client_user)[:1].upper() or "?",
        "subject_name": sub.name,
        "review_date": review.reviewDate.strftime("%b %Y"),
        "rating": review.rating,
        "comment": review.comment,
        **stars(review.rating),
    }


def payment_row(payment):
    booking = payment.bookingID
    sub = booking.tutorSubjectID.subjectID
    tutor_user = booking.tutorSubjectID.tutorID.userID
    client_user = booking.clientID.userID
    return {
        "paymentId": payment.paymentId,
        "booking_id": booking.bookingId,
        "subject_name": sub.name,
        "tutor_name": f"{first_name(tutor_user)} {last_name_initial(tutor_user)}.",
        "client_name": f"{first_name(client_user)} {last_name_initial(client_user)}.",
        "method": payment.method,
        "status": payment.get_status_display(),
        "amount": payment.amount,
        "processed_at": payment.processedAt.strftime("%b %d, %Y"),
    }


def payment_summary(payments):
    today = date.today()
    total_spent = sum((p.amount for p in payments if p.status == "processed"), start=0)
    total_payments = sum(1 for p in payments if p.status == "processed")
    month_spent = sum(
        (p.amount for p in payments
         if p.status == "processed"
         and p.processedAt.year == today.year
         and p.processedAt.month == today.month),
        start=0,
    )
    month_payments = sum(
        1 for p in payments
        if p.status == "processed"
        and p.processedAt.year == today.year
        and p.processedAt.month == today.month
    )
    total_refunded = sum((p.amount for p in payments if p.status == "refunded"), start=0)
    refund_count = sum(1 for p in payments if p.status == "refunded")
    return {
        "total_spent": f"{total_spent:.2f}",
        "total_payments": total_payments,
        "month_spent": f"{month_spent:.2f}",
        "month_payments": month_payments,
        "total_refunded": f"{total_refunded:.2f}",
        "refund_count": refund_count,
    }


def inbox_row(message, me):
    other = message.senderUserId if message.receiverUserId_id == me.userId else message.receiverUserId
    body = message.body or ""
    return {
        "messageId": message.messageId,
        "other_user_id": other.userId,
        "sender_name": f"{first_name(other)} {last_name_initial(other)}.",
        "sender_initial": first_name(other)[:1].upper() or "?",
        "preview": (body[:120] + "…") if len(body) > 120 else body,
        "sent_at_display": message.sentAt.strftime("%b %d, %I:%M %p").replace(" 0", " "),
        "is_read": message.isRead,
    }


def conversation_data(other_user, me):
    from .models import Tutor

    is_tutor = False
    subjects_summary = ""
    tutor_id = None
    try:
        tp = other_user.tutor_profile
        is_tutor = True
        tutor_id = tp.tutorId
        subjects = list(tp.tutor_subjects.select_related("subjectID")[:3])
        subjects_summary = ", ".join(s.subjectID.name for s in subjects)
    except Tutor.DoesNotExist:
        pass
    return {
        "userId": other_user.userId,
        "first_name": first_name(other_user),
        "last_name_initial": last_name_initial(other_user),
        "initial": first_name(other_user)[:1].upper() or "?",
        "is_tutor": is_tutor,
        "subjects_summary": subjects_summary,
        "tutor_id": tutor_id,
    }


def thread_message(message, me):
    return {
        "messageId": message.messageId,
        "is_me": message.senderUserId_id == me.userId,
        "body": message.body,
        "sent_at_display": message.sentAt.strftime("%b %d, %I:%M %p").replace(" 0", " "),
    }


def thread_messages(messages, me):
    return [thread_message(m, me) for m in messages]


def availability_grid(tutor):
    by_day = {d: [] for d in DAY_ORDER}
    for slot in tutor.availabilities.order_by("startTime"):
        by_day.setdefault(slot.dayOfWeek, []).append(slot)
    return [{
        "short_name": DAY_SHORT.get(d, d.title()),
        "slots": [{
            "availabilityId": s.availabilityId,
            "start_time": s.startTime.strftime("%I:%M %p").lstrip("0"),
            "end_time": s.endTime.strftime("%I:%M %p").lstrip("0"),
        } for s in by_day[d]],
    } for d in DAY_ORDER]
