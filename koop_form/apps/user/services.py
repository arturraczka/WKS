from django.conf import settings


def get_user_fund(user):
    if hasattr(user, "userprofile"):
        return user.userprofile.fund.value
    return settings.DEFAULT_USER_FUND
