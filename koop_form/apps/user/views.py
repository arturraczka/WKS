from django.contrib.auth.views import LogoutView


class CustomLogoutView(LogoutView):
    http_method_names = ["get", "head", "post", "options"]
