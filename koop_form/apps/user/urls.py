from django.urls import path
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)

from apps.user.views import CustomLogoutView

urlpatterns = [
    path(
        "zaloguj/",
        LoginView.as_view(
            template_name="user/login.html", next_page="order-update-form"
        ),
        name="login",
    ),
    path(
        "wylogowano/",
        CustomLogoutView.as_view(template_name="user/logout.html"),
        name="logout",
    ),
    path(
        "zmiana-hasla/",
        PasswordChangeView.as_view(template_name="user/password-change-confirm.html"),
        name="password_change_request",
    ),
    path(
        "zmiana-hasla/sukces/",
        PasswordChangeDoneView.as_view(template_name="user/password-change-done.html"),
        name="password_change_done",
    ),
    path(
        "reset-hasla/",
        PasswordResetView.as_view(template_name="user/password-reset-request.html"),
        name="password_reset_request",
    ),
    path(
        "reset-hasla/wyslano/",
        PasswordResetDoneView.as_view(template_name="user/password-reset-done.html"),
        name="password_reset_done",
    ),
    path(
        "reset-hasla/potwierdzenie/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="user/password-reset-confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset-hasla/sukces/",
        PasswordResetCompleteView.as_view(
            template_name="user/password-reset-complete.html"
        ),
        name="password_reset_complete",
    ),
]
