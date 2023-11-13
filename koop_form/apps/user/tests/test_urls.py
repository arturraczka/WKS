from django.urls import reverse
from django.test import TestCase

from apps.form.tests.factories import UserFactory


class TestLoginView(TestCase):
    def setUp(self):
        self.url = reverse('login')

    def test_response(self):
        response = self.client.get(self.url)
        assert response.status_code == 200


class TestLogoutView(TestCase):
    def setUp(self):
        self.url = reverse('logout')

    def test_response(self):
        response = self.client.get(self.url)
        assert response.status_code == 200


class TestPasswordChangeView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.url = reverse('password_change_request')

    def test_response(self):
        response = self.client.get(self.url)
        assert response.status_code == 200


class TestPasswordChangeDoneView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.url = reverse('password_change_done')

    def test_response(self):
        response = self.client.get(self.url)
        assert response.status_code == 200


class TestPasswordResetView(TestCase):
    def setUp(self):
        self.url = reverse('password_reset_request')

    def test_response(self):
        response = self.client.get(self.url)
        assert response.status_code == 200


class TestPasswordResetDoneView(TestCase):
    def setUp(self):
        self.url = reverse('password_reset_done')

    def test_response(self):
        response = self.client.get(self.url)
        assert response.status_code == 200


class TestPasswordResetConfirmView(TestCase):
    def setUp(self):
        self.url = reverse('password_reset_confirm', kwargs={"uidb64": None, "token": None})

    def test_response(self):
        response = self.client.get(self.url)
        assert response.status_code == 200


class TestPasswordResetCompleteView(TestCase):
    def setUp(self):
        self.url = reverse('password_reset_complete')

    def test_response(self):
        response = self.client.get(self.url)
        assert response.status_code == 200
