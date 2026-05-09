import re

from django import forms
from django.contrib.auth import get_user_model, password_validation
from .models import (
    Tutor, Client, Subject, TutorSubject, Credential,
    Availability, Location, Booking, Review, Message,
)

User = get_user_model()


def clean_us_phone(value):
    value = (value or "").strip()
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise forms.ValidationError("Enter a valid 10-digit phone number.")
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

# ── Auth ──────────────────────────────────────────────────────────────────

class RegisterForm(forms.Form):
    USER_TYPE_CHOICES = [("tutor", "I'm a Tutor"), ("client", "I'm a Student / Parent")]
    first_name = forms.CharField(max_length=30, label="First Name")
    last_name = forms.CharField(max_length=30, label="Last Name")
    email = forms.EmailField()
    phone = forms.CharField(
        max_length=20,
        error_messages={"required": "Phone number is required."},
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8,
        error_messages={"min_length": "Password must be at least 8 characters."},
    )
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.RadioSelect)

    def clean_phone(self):
        return clean_us_phone(self.cleaned_data["phone"])

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm_password = cleaned.get("confirm_password")
        email = cleaned.get("email")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        if password:
            pending_user = User(
                username=email or "",
                email=email or "",
                first_name=cleaned.get("first_name") or "",
                last_name=cleaned.get("last_name") or "",
                firstName=cleaned.get("first_name") or "",
                lastName=cleaned.get("last_name") or "",
            )
            try:
                password_validation.validate_password(password, pending_user)
            except forms.ValidationError as exc:
                self.add_error("password", exc)

        if email and User.objects.filter(email=email).exists():
            self.add_error("email", "An account with this email already exists.")
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class PasswordReminderForm(forms.Form):
    email = forms.EmailField()


# ── Tutor Profile ─────────────────────────────────────────────────────────

class TutorProfileForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    phone = forms.CharField(
        max_length=20,
        error_messages={"required": "Phone number is required."},
    )
    bio = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)
    service_radius = forms.IntegerField(min_value=1, max_value=100, label="Service Radius (miles)")

    def clean_phone(self):
        return clean_us_phone(self.cleaned_data["phone"])


class CredentialForm(forms.ModelForm):
    class Meta:
        model = Credential
        fields = ["type", "issuingInstitution", "documentURL", "issueDate"]
        labels = {
            "type": "Credential Type",
            "issuingInstitution": "Issuing Institution",
            "documentURL": "Document URL",
            "issueDate": "Issue Date",
        }
        widgets = {"issueDate": forms.DateInput(attrs={"type": "date"})}


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ["dayOfWeek", "startTime", "endTime", "isRecurring", "recurringEndDate"]
        labels = {
            "dayOfWeek": "Day of Week",
            "startTime": "Start Time",
            "endTime": "End Time",
            "isRecurring": "Recurring?",
            "recurringEndDate": "Recurring Until",
        }
        widgets = {
            "startTime": forms.TimeInput(attrs={"type": "time"}),
            "endTime": forms.TimeInput(attrs={"type": "time"}),
            "recurringEndDate": forms.DateInput(attrs={"type": "date"}),
        }


class TutorSubjectForm(forms.Form):
    subject = forms.CharField(
        max_length=50,
        label="Subject",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Algebra II, AP Biology, Spanish"}),
    )
    ratePerHour = forms.DecimalField(
        max_digits=8, decimal_places=2, label="Rate Per Hour ($)",
    )
    skillLevel = forms.ChoiceField(
        choices=TutorSubject.SKILL_LEVEL_CHOICES,
        label="Skill Level",
        initial="intermediate",
    )


# ── Client / Booking ─────────────────────────────────────────────────────

class SearchTutorsForm(forms.Form):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(), required=False, empty_label="Any Subject"
    )
    zip_code = forms.CharField(max_length=20, required=False, label="Zip Code")
    max_distance = forms.IntegerField(required=False, min_value=1, label="Max Distance (mi)")
    day_of_week = forms.ChoiceField(
        choices=[("", "Any Day")] + Availability.DAY_CHOICES, required=False
    )
    start_time = forms.TimeField(
        required=False, widget=forms.TimeInput(attrs={"type": "time"})
    )
    verified_only = forms.BooleanField(required=False, label="Verified Tutors Only")


class BookingForm(forms.Form):
    tutor_subject = forms.ModelChoiceField(queryset=TutorSubject.objects.none(), label="Subject")
    availability = forms.ModelChoiceField(queryset=Availability.objects.none(), label="Time Slot")
    scheduled_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), label="Date")
    duration_minutes = forms.IntegerField(min_value=30, max_value=240, initial=60, label="Duration (min)")
    street = forms.CharField(max_length=150)
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    zip_code = forms.CharField(max_length=20)
    payment_method = forms.ChoiceField(choices=[
        ("credit_card", "Credit Card"),
        ("debit_card", "Debit Card"),
        ("paypal", "PayPal"),
    ])


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "comment": forms.Textarea(attrs={"rows": 4}),
        }


# ── Messaging ─────────────────────────────────────────────────────────────

class MessageForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Type your message…"})
    )
