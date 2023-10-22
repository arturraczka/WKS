from django.contrib.auth.mixins import UserPassesTestMixin


class OrderExistsTestMixin(UserPassesTestMixin):
    login_url = "/formularz/zamowienie/nowe/"
    permission_denied_message = "Najpierw utwórz nowe zamówienie na ten tydzień."
