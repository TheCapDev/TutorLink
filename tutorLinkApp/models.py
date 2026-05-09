from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    userId = models.AutoField(primary_key=True)
    firstName = models.CharField(max_length=30)
    lastName = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    passwordHash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.firstName} {self.lastName} ({self.email})"


class Tutor(models.Model):
    tutorId = models.AutoField(primary_key=True)
    userID = models.OneToOneField(User, on_delete=models.CASCADE, related_name="tutor_profile")
    bio = models.TextField(blank=True)
    serviceRadiusMiles = models.PositiveIntegerField(default=10)
    isVerified = models.BooleanField(default=False)

    def __str__(self):
        return f"Tutor: {self.userID}"


class Client(models.Model):
    clientId = models.AutoField(primary_key=True)
    userID = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")
    preferredLearnerName = models.CharField(max_length=50, blank=True)
    relationshipToLearner = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Client: {self.userID}"


class Subject(models.Model):
    subjectId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=50)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.category})"


class TutorSubject(models.Model):
    TutorSubjectId = models.AutoField(primary_key=True)
    SKILL_LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
        ("expert", "Expert"),
    ]
    tutorID = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="tutor_subjects")
    subjectID = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="tutor_subjects")
    ratePerHour = models.DecimalField(max_digits=8, decimal_places=2)
    skillLevel = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES, default="intermediate")

    class Meta:
        unique_together = ["tutorID", "subjectID"]

    def __str__(self):
        return f"{self.tutorID.userID.firstName} — {self.subjectID.name} (${self.ratePerHour}/hr)"


class Credential(models.Model):
    credentialId = models.AutoField(primary_key=True)
    tutorID = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="credentials")
    type = models.CharField(max_length=100)
    issuingInstitution = models.CharField(max_length=255)
    documentURL = models.URLField(blank=True)
    issueDate = models.DateField()

    def __str__(self):
        return f"{self.type} — {self.issuingInstitution}"


class BackgroundCheck(models.Model):
    checkId = models.AutoField(primary_key=True)
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("passed", "Passed"),
        ("failed", "Failed"),
    ]
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="background_checks")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    provider = models.CharField(max_length=255)
    dateCompleted = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Check for {self.tutor} — {self.status}"


class Availability(models.Model):
    availabilityId = models.AutoField(primary_key=True)
    DAY_CHOICES = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
        ("saturday", "Saturday"),
        ("sunday", "Sunday"),
    ]
    tutorID = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name="availabilities")
    dayOfWeek = models.CharField(max_length=20, choices=DAY_CHOICES)
    startTime = models.TimeField()
    endTime = models.TimeField()
    isRecurring = models.BooleanField(default=True)
    recurringEndDate = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "availabilities"

    def __str__(self):
        return f"{self.tutorID} — {self.dayOfWeek} {self.startTime}–{self.endTime}"


class Location(models.Model):
    locationId = models.AutoField(primary_key=True)
    street = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"


class Booking(models.Model):
    bookingId = models.AutoField(primary_key=True)
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    clientID = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bookings")
    tutorSubjectID = models.ForeignKey(TutorSubject, on_delete=models.CASCADE, related_name="bookings")
    availabilityId = models.ForeignKey(Availability, on_delete=models.SET_NULL, null=True, related_name="bookings")
    locationID = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name="bookings")
    scheduledDateTime = models.DateTimeField()
    durationMinutes = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.pk}: {self.clientID} → {self.tutorSubjectID.tutorID} — {self.status}"


class Payment(models.Model):
    paymentId = models.AutoField(primary_key=True)
    STATUS_CHOICES = [
        ("processed", "Processed"),
        ("refunded", "Refunded"),
        ("failed", "Failed"),
    ]
    bookingID = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="processed")
    method = models.CharField(max_length=50)
    processedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.pk} — ${self.amount} ({self.status})"


class Message(models.Model):
    messageId = models.AutoField(primary_key=True)
    senderUserId = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiverUserId = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    body = models.TextField()
    sentAt = models.DateTimeField(auto_now_add=True)
    isRead = models.BooleanField(default=False)

    class Meta:
        ordering = ["-sentAt"]

    def __str__(self):
        return f"Message from {self.senderUserId} to {self.receiverUserId} at {self.sentAt}"


class Review(models.Model):
    reviewId = models.AutoField(primary_key=True)
    bookingID = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="review")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    reviewDate = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Review for Booking #{self.bookingID.pk} — {self.rating}/5"
