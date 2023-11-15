from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse


class OrderExistsTestMixin(UserPassesTestMixin):
    def get_permission_denied_message(self):
        return "Najpierw utwórz nowe zamówienie na ten tydzień."

    def get_login_url(self):
        """
        Override this method to return the specific URL where you want to
        redirect the user in case the test fails.
        """
        # You can return a specific URL here.
        return reverse('order-create')

    def handle_no_permission(self):
        return redirect(self.get_login_url())
