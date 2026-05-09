from .models import Tutor, Client


def user_type(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"user_type": None}
    try:
        request.user.tutor_profile
        return {"user_type": "tutor"}
    except Tutor.DoesNotExist:
        pass
    try:
        request.user.client_profile
        return {"user_type": "client"}
    except Client.DoesNotExist:
        pass
    return {"user_type": None}
