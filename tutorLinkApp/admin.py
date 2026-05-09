from django.contrib import admin
# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Tutor, Client, Subject, TutorSubject, Credential,
    BackgroundCheck, Availability, Location, Booking, Payment, Message, Review,
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
  list_display = ("email", "firstName", "lastName", "is_staff")
  search_fields = ("email", "firstName", "lastName")
  ordering = ("email",)


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
  list_display = ("userID", "isVerified", "serviceRadiusMiles")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
  list_display = ("userID", "preferredLearnerName", "relationshipToLearner")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
  list_display = ("name", "category")
  list_filter = ("category",)


@admin.register(TutorSubject)
class TutorSubjectAdmin(admin.ModelAdmin):
  list_display = ("tutorID", "subjectID", "ratePerHour", "skillLevel")


admin.site.register(Credential)
admin.site.register(BackgroundCheck)
admin.site.register(Availability)
admin.site.register(Location)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
  list_display = ("bookingId", "clientID", "tutorSubjectID", "status", "scheduledDateTime")
  list_filter = ("status",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
  list_display = ("paymentId", "bookingID", "amount", "status", "method")
  list_filter = ("status",)

admin.site.register(Message)
admin.site.register(Review)
