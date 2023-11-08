from django.urls import path
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)

urlpatterns = [
    path(
        "logowanie/",
        LoginView.as_view(template_name="user/login.html", next_page="order-producers"),
        name="login",
    ),
    path(
        "wylogowanie/", LogoutView.as_view(template_name="user/logout.html"), name="logout"
    ),
    path(
        "zmiana-hasla/sukces/",
        PasswordChangeDoneView.as_view(
            template_name="user/password_reset_complete.html"
        ),
        name="password-change-done",
    ),
    path(
        "zmiana-hasla/prosba/",
        PasswordChangeView.as_view(template_name="user/password_reset_confirm.html"),
        name="password-change-request",
    ),
    path(
        "reset-hasla/wyslany/",
        PasswordResetCompleteView.as_view(
            template_name="user/password_reset_complete.html"
        ),
        name="password-reset-complete",
    ),
    path(
        "reset-hasla/potwierdzenie/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="user/password_reset_confirm.html"
        ),
        name="password-reset-confirm",
    ),
    path(
        "reset-hasla/sukces/",
        PasswordResetDoneView.as_view(template_name="user/password_reset_done.html"),
        name="password-reset-done",
    ),
    path(
        "reset-hasla/prosba/",
        PasswordResetView.as_view(template_name="user/password_reset_request.html"),
        name="password-reset-request",
    ),
]
