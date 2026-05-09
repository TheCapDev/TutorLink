"""
URL configuration for tutorLink project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    # Public
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("password-reminder/", views.password_reminder, name="password_reminder"),

    # Tutor
    path("tutor/dashboard/", views.tutor_dashboard, name="tutor_dashboard"),
    path("tutor/profile/edit/", views.edit_tutor_profile, name="edit_tutor_profile"),
    path("tutor/credentials/", views.manage_credentials, name="manage_credentials"),
    path("tutor/availability/", views.manage_availability, name="manage_availability"),
    path("tutor/subjects/", views.manage_subjects, name="manage_subjects"),
    path("tutor/reviews/", views.tutor_reviews, name="tutor_reviews"),

    # Client
    path("client/dashboard/", views.client_dashboard, name="client_dashboard"),
    path("search/", views.search_tutors, name="search_tutors"),
    path("tutor/<int:tutor_id>/", views.tutor_profile, name="tutor_profile"),
    path("tutor/<int:tutor_id>/book/", views.create_booking, name="create_booking"),
    path("review/<int:booking_id>/", views.submit_review, name="submit_review"),
    path("payments/", views.payment_history, name="payment_history"),

    # Shared
    path("bookings/", views.view_bookings, name="view_bookings"),
    path("messages/", views.messages_inbox, name="messages_inbox"),
    path("messages/conversation/<int:other_user_id>/", views.conversation, name="conversation"),
]