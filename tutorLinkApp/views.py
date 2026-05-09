from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.http import Http404

from .models import (
    Tutor, Client, Subject, TutorSubject, Credential,
    Availability, Location, Booking,
    Payment, Message, Review,
)
from .forms import (
    RegisterForm, LoginForm, PasswordReminderForm,
    TutorProfileForm, CredentialForm, AvailabilityForm, TutorSubjectForm,
    SearchTutorsForm, BookingForm, ReviewForm, MessageForm,
)
from . import display

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────

def _user_type(user):
    try:
        user.tutor_profile
        return "tutor"
    except Tutor.DoesNotExist:
        pass
    try:
        user.client_profile
        return "client"
    except Client.DoesNotExist:
        pass
    return None


def _dashboard(user):
    utype = _user_type(user)
    if utype == "tutor":
        return "/tutor/dashboard/"
    elif utype == "client":
        return "/client/dashboard/"
    return "/admin/"


def _next_booking_when(booking):
    if booking is None:
        return "No sessions scheduled"
    return booking.scheduledDateTime.strftime("%a %b %d, %I:%M %p").replace(" 0", " ")


# ── Public Pages ──────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated and _user_type(request.user) in ("tutor", "client"):
        return redirect(_dashboard(request.user))
    featured_qs = (
        Tutor.objects
        .filter(isVerified=True)
        .select_related("userID")
        .annotate(
            avg_rating=Avg("tutor_subjects__bookings__review__rating"),
            review_count=Count("tutor_subjects__bookings__review"),
        )
        .order_by("-avg_rating")[:6]
    )
    featured = [display.tutor_card(t) for t in featured_qs]
    subjects = Subject.objects.all()
    return render(request, "home.html", {"featured_tutors": featured, "subjects": subjects})


def login_view(request):
    if request.user.is_authenticated and _user_type(request.user) in ("tutor", "client"):
        return redirect(_dashboard(request.user))
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            user_obj = None
        if user_obj and user_obj.check_password(password):
            login(request, user_obj)
            return redirect(_dashboard(user_obj))
        form.add_error(None, "Invalid email or password.")
    return render(request, "auth/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated and _user_type(request.user) in ("tutor", "client"):
        return redirect(_dashboard(request.user))
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        user = User(
            username=d["email"],
            email=d["email"],
            firstName=d["first_name"],
            lastName=d["last_name"],
            first_name=d["first_name"],
            last_name=d["last_name"],
            phone=d.get("phone", ""),
        )
        user.set_password(d["password"])
        user.save()
        if d["user_type"] == "tutor":
            Tutor.objects.create(userID=user)
        else:
            Client.objects.create(userID=user)
        login(request, user)
        return redirect(_dashboard(user))
    return render(request, "auth/register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/")


def password_reminder(request):
    form = PasswordReminderForm(request.POST or None)
    sent = False
    if request.method == "POST" and form.is_valid():
        sent = True
        messages.success(request, "If that email is registered, a reset link has been sent.")
    return render(request, "auth/password_reminder.html", {"form": form, "sent": sent})


# ── Tutor Pages ───────────────────────────────────────────────────────────

@login_required
def tutor_dashboard(request):
    tutor = get_object_or_404(Tutor, userID=request.user)
    now = timezone.now()
    upcoming_qs = Booking.objects.filter(
        tutorSubjectID__tutorID=tutor,
        status__in=["pending", "confirmed"],
        scheduledDateTime__gte=now,
    ).select_related(
        "tutorSubjectID__subjectID", "clientID__userID",
        "tutorSubjectID__tutorID__userID", "locationID",
    ).order_by("scheduledDateTime")
    upcoming_bookings = [display.booking_row(b, "tutor") for b in upcoming_qs[:5]]
    upcoming_count = upcoming_qs.count()
    next_when = _next_booking_when(upcoming_qs.first())

    unread = Message.objects.filter(receiverUserId=request.user, isRead=False).count()

    review_agg = Review.objects.filter(
        bookingID__tutorSubjectID__tutorID=tutor
    ).aggregate(avg=Avg("rating"), count=Count("rating"))
    avg_rating = display.format_rating(review_agg["avg"])
    review_count = review_agg["count"] or 0

    bg = tutor.background_checks.order_by("-dateCompleted").first()
    check_status = bg.get_status_display().lower() if bg else "in progress"

    return render(request, "tutor/dashboard.html", {
        "tutor": tutor,
        "is_verified": tutor.isVerified,
        "upcoming_bookings_count": upcoming_count,
        "upcoming_bookings": upcoming_bookings,
        "unread_messages_count": unread,
        "next_booking_when": next_when,
        "avg_rating": avg_rating,
        "review_count": review_count,
        "check_status": check_status,
    })


@login_required
def edit_tutor_profile(request):
    tutor = get_object_or_404(Tutor, userID=request.user)
    user = request.user
    if request.method == "POST":
        form = TutorProfileForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user.firstName = d["first_name"]
            user.first_name = d["first_name"]
            user.lastName = d["last_name"]
            user.last_name = d["last_name"]
            user.phone = d["phone"]
            user.save()
            tutor.bio = d["bio"]
            tutor.serviceRadiusMiles = d["service_radius"]
            tutor.save()
            messages.success(request, "Profile updated.")
            return redirect("/tutor/dashboard/")
    else:
        form = TutorProfileForm(initial={
            "first_name": display.first_name(user),
            "last_name": display.last_name(user),
            "phone": user.phone,
            "bio": tutor.bio,
            "service_radius": tutor.serviceRadiusMiles,
        })
    tutor_vm = {
        "first_name": display.first_name(user),
        "last_name": display.last_name(user),
        "phone": user.phone,
        "bio": tutor.bio,
        "service_radius_miles": tutor.serviceRadiusMiles,
    }
    return render(request, "tutor/edit_profile.html", {"form": form, "tutor": tutor_vm})


@login_required
def manage_credentials(request):
    tutor = get_object_or_404(Tutor, userID=request.user)
    if request.method == "POST":
        if "delete_id" in request.POST:
            Credential.objects.filter(credentialId=request.POST["delete_id"], tutorID=tutor).delete()
            messages.success(request, "Credential removed.")
            return redirect("/tutor/credentials/")
        form = CredentialForm(request.POST)
        if form.is_valid():
            cred = form.save(commit=False)
            cred.tutorID = tutor
            cred.save()
            messages.success(request, "Credential added.")
            return redirect("/tutor/credentials/")
    else:
        form = CredentialForm()
    creds = [{
        "credentialId": c.credentialId,
        "type": c.type,
        "issuing_institution": c.issuingInstitution,
        "issue_date": c.issueDate,
        "document_url": c.documentURL,
    } for c in tutor.credentials.order_by("-issueDate")]
    return render(request, "tutor/manage_credentials.html", {"form": form, "credentials": creds})


@login_required
def manage_availability(request):
    tutor = get_object_or_404(Tutor, userID=request.user)
    if request.method == "POST":
        if "delete_id" in request.POST:
            Availability.objects.filter(availabilityId=request.POST["delete_id"], tutorID=tutor).delete()
            messages.success(request, "Slot removed.")
            return redirect("/tutor/availability/")
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.tutorID = tutor
            slot.save()
            messages.success(request, "Availability added.")
            return redirect("/tutor/availability/")
    else:
        form = AvailabilityForm()
    return render(request, "tutor/manage_availability.html", {
        "form": form, "days": display.availability_grid(tutor),
    })


@login_required
def manage_subjects(request):
    tutor = get_object_or_404(Tutor, userID=request.user)
    if request.method == "POST":
        if "delete_id" in request.POST:
            TutorSubject.objects.filter(TutorSubjectId=request.POST["delete_id"], tutorID=tutor).delete()
            messages.success(request, "Subject removed.")
            return redirect("/tutor/subjects/")
        form = TutorSubjectForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            name = d["subject"].strip()
            subject = Subject.objects.filter(name__iexact=name).first()
            if subject is None:
                subject = Subject.objects.create(name=name, category="Other")
            if TutorSubject.objects.filter(tutorID=tutor, subjectID=subject).exists():
                form.add_error("subject", f"You already teach {subject.name}.")
            else:
                TutorSubject.objects.create(
                    tutorID=tutor,
                    subjectID=subject,
                    ratePerHour=d["ratePerHour"],
                    skillLevel=d["skillLevel"],
                )
                messages.success(request, "Subject added.")
                return redirect("/tutor/subjects/")
    else:
        form = TutorSubjectForm()
    subjects = tutor.tutor_subjects.select_related("subjectID").all()
    return render(request, "tutor/manage_subjects.html", {"form": form, "subjects": subjects})


@login_required
def tutor_reviews(request):
    tutor = get_object_or_404(Tutor, userID=request.user)
    reviews_qs = (
        Review.objects
        .filter(bookingID__tutorSubjectID__tutorID=tutor)
        .select_related("bookingID__clientID__userID", "bookingID__tutorSubjectID__subjectID")
        .order_by("-reviewDate")
    )
    agg = reviews_qs.aggregate(avg=Avg("rating"), count=Count("rating"))
    avg = agg["avg"]
    review_count = agg["count"] or 0
    reviews = [display.review_row(r) for r in reviews_qs]
    return render(request, "tutor/view_reviews.html", {
        "reviews": reviews,
        "avg_rating": display.format_rating(avg),
        "review_count": review_count,
        **display.stars(avg),
    })


# ── Client Pages ──────────────────────────────────────────────────────────

@login_required
def client_dashboard(request):
    client = get_object_or_404(Client, userID=request.user)
    now = timezone.now()
    upcoming_qs = Booking.objects.filter(
        clientID=client,
        status__in=["pending", "confirmed"],
        scheduledDateTime__gte=now,
    ).select_related(
        "tutorSubjectID__subjectID", "tutorSubjectID__tutorID__userID",
        "clientID__userID", "locationID",
    ).order_by("scheduledDateTime")
    upcoming_bookings = [display.booking_row(b, "client") for b in upcoming_qs[:5]]
    upcoming_count = upcoming_qs.count()
    next_when = _next_booking_when(upcoming_qs.first())

    unread = Message.objects.filter(receiverUserId=request.user, isRead=False).count()
    pending_reviews = Booking.objects.filter(
        clientID=client, status="completed", review__isnull=True,
    ).count()

    return render(request, "client/dashboard.html", {
        "client": client,
        "upcoming_bookings_count": upcoming_count,
        "upcoming_bookings": upcoming_bookings,
        "unread_messages_count": unread,
        "pending_reviews_count": pending_reviews,
        "next_booking_when": next_when,
    })


@login_required
def search_tutors(request):
    form = SearchTutorsForm(request.GET or None)
    tutors_qs = Tutor.objects.select_related("userID").annotate(
        avg_rating=Avg("tutor_subjects__bookings__review__rating"),
        review_count=Count("tutor_subjects__bookings__review"),
    )
    if form.is_valid():
        d = form.cleaned_data
        if d.get("subject"):
            tutors_qs = tutors_qs.filter(tutor_subjects__subjectID=d["subject"])
        if d.get("day_of_week"):
            tutors_qs = tutors_qs.filter(availabilities__dayOfWeek=d["day_of_week"])
        if d.get("start_time"):
            tutors_qs = tutors_qs.filter(
                availabilities__startTime__lte=d["start_time"],
                availabilities__endTime__gte=d["start_time"],
            )
        if d.get("verified_only"):
            tutors_qs = tutors_qs.filter(isVerified=True)
    tutors_qs = tutors_qs.distinct()
    tutors = [display.tutor_card(t) for t in tutors_qs]
    subjects = [{"subject_id": s.subjectId, "name": s.name, "selected": False} for s in Subject.objects.all()]
    filters = form.data if form.is_valid() else {}
    return render(request, "client/search_tutors.html", {
        "form": form, "tutors": tutors, "subjects": subjects,
        "result_count": len(tutors), "filters": filters,
    })


@login_required
def tutor_profile(request, tutor_id):
    tutor = get_object_or_404(Tutor.objects.select_related("userID"), tutorId=tutor_id)
    return render(request, "client/tutor_profile.html", {
        "tutor": display.tutor_profile(tutor),
    })


@login_required
def create_booking(request, tutor_id):
    tutor = get_object_or_404(Tutor.objects.select_related("userID"), tutorId=tutor_id)
    client = get_object_or_404(Client, userID=request.user)
    form = BookingForm(request.POST or None)
    form.fields["tutor_subject"].queryset = tutor.tutor_subjects.select_related("subjectID")
    form.fields["availability"].queryset = tutor.availabilities.all()

    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        loc = Location.objects.create(
            street=d["street"], city=d["city"], state=d["state"], zip_code=d["zip_code"],
        )
        ts = d["tutor_subject"]
        sched = timezone.make_aware(datetime.combine(d["scheduled_date"], d["availability"].startTime))
        booking = Booking.objects.create(
            clientID=client,
            tutorSubjectID=ts,
            availabilityId=d["availability"],
            locationID=loc,
            scheduledDateTime=sched,
            durationMinutes=d["duration_minutes"],
            status="pending",
        )
        amount = ts.ratePerHour * Decimal(d["duration_minutes"]) / Decimal(60)
        Payment.objects.create(
            bookingID=booking, amount=amount, method=d["payment_method"], status="processed",
        )
        messages.success(request, "Booking created and payment processed!")
        return redirect("/bookings/")

    return render(request, "client/create_booking.html", {
        "form": form,
        "tutor": display.tutor_profile(tutor),
        "today": timezone.localdate().isoformat(),
    })


@login_required
def submit_review(request, booking_id):
    booking = get_object_or_404(Booking, bookingId=booking_id, status="completed")
    client = get_object_or_404(Client, userID=request.user)
    if booking.clientID != client:
        raise Http404
    if hasattr(booking, "review"):
        messages.info(request, "You already reviewed this booking.")
        return redirect("/bookings/")
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.bookingID = booking
        review.save()
        messages.success(request, "Review submitted!")
        return redirect("/bookings/")
    return render(request, "client/submit_review.html", {
        "form": form,
        "booking": display.booking_row(booking, "client"),
    })


@login_required
def payment_history(request):
    utype = _user_type(request.user)
    if utype == "client":
        client = request.user.client_profile
        payments_qs = Payment.objects.filter(bookingID__clientID=client)
    elif utype == "tutor":
        tutor = request.user.tutor_profile
        payments_qs = Payment.objects.filter(bookingID__tutorSubjectID__tutorID=tutor)
    else:
        payments_qs = Payment.objects.none()
    payments_qs = payments_qs.select_related(
        "bookingID__tutorSubjectID__subjectID",
        "bookingID__tutorSubjectID__tutorID__userID",
        "bookingID__clientID__userID",
    ).order_by("-processedAt")
    payments_list = list(payments_qs)
    payments = [display.payment_row(p) for p in payments_list]
    summary = display.payment_summary(payments_list)
    return render(request, "client/payment_history.html", {
        "payments": payments, **summary,
    })


# ── Shared Pages ──────────────────────────────────────────────────────────

@login_required
def view_bookings(request):
    utype = _user_type(request.user)
    if utype == "client":
        client = request.user.client_profile
        bookings_qs = Booking.objects.filter(clientID=client)
    elif utype == "tutor":
        tutor = request.user.tutor_profile
        bookings_qs = Booking.objects.filter(tutorSubjectID__tutorID=tutor)
    else:
        bookings_qs = Booking.objects.none()

    if request.method == "POST":
        if utype not in ("client", "tutor"):
            raise Http404
        bid = request.POST.get("booking_id")
        action = request.POST.get("action")
        booking = get_object_or_404(bookings_qs, bookingId=bid)
        if action == "confirm" and utype == "tutor" and booking.status == "pending":
            booking.status = "confirmed"
            booking.save()
            messages.success(request, "Booking confirmed.")
        elif action == "cancel" and booking.status in ["pending", "confirmed"]:
            booking.status = "cancelled"
            booking.save()
            if hasattr(booking, "payment") and booking.payment.status == "processed":
                booking.payment.status = "refunded"
                booking.payment.save()
            messages.success(request, "Booking cancelled.")
        elif action == "complete" and utype == "tutor" and booking.status == "confirmed":
            booking.status = "completed"
            booking.save()
            messages.success(request, "Booking marked complete.")
        return redirect("/bookings/")

    bookings_qs = bookings_qs.select_related(
        "tutorSubjectID__subjectID", "tutorSubjectID__tutorID__userID",
        "clientID__userID", "locationID", "payment", "review",
    ).order_by("-scheduledDateTime")
    upcoming, pending, past, cancelled = display.split_bookings(
        list(bookings_qs), utype, timezone.now()
    )
    return render(request, "shared/view_bookings.html", {
        "user_type": utype,
        "upcoming_bookings": upcoming,
        "pending_bookings": pending,
        "past_bookings": past,
        "cancelled_bookings": cancelled,
        "upcoming_count": len(upcoming),
        "pending_count": len(pending),
        "past_count": len(past),
        "cancelled_count": len(cancelled),
    })


@login_required
def messages_inbox(request):
    inbox_qs = (
        Message.objects
        .filter(receiverUserId=request.user)
        .select_related("senderUserId", "receiverUserId")
        .order_by("-sentAt")
    )
    inbox = [display.inbox_row(m, request.user) for m in inbox_qs]
    unread = sum(1 for m in inbox if not m["is_read"])
    return render(request, "shared/messages_inbox.html", {
        "inbox": inbox, "unread_count": unread,
    })


@login_required
def conversation(request, other_user_id):
    other = get_object_or_404(User, userId=other_user_id)
    me = request.user

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(
                senderUserId=me, receiverUserId=other, body=form.cleaned_data["body"],
            )
            return redirect(f"/messages/conversation/{other_user_id}/")
    else:
        form = MessageForm()

    Message.objects.filter(senderUserId=other, receiverUserId=me, isRead=False).update(isRead=True)

    msgs = (
        Message.objects
        .filter(
            Q(senderUserId=me, receiverUserId=other) |
            Q(senderUserId=other, receiverUserId=me)
        )
        .order_by("sentAt")
    )
    return render(request, "shared/conversation.html", {
        "thread": display.thread_messages(msgs, me),
        "other_user": display.conversation_data(other, me),
        "form": form,
    })
