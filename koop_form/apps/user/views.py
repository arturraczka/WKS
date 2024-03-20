from django.contrib.auth.views import LogoutView, LoginView, PasswordResetView, PasswordResetConfirmView

from apps.user.forms import CustomLoginForm, CustomPasswordResetForm, CustomSetPasswordForm


class CustomLogoutView(LogoutView):
    http_method_names = ["get", "head", "post", "options"]


class CustomLoginView(LoginView):
    form_class = CustomLoginForm


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
