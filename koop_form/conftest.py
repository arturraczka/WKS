from decimal import Decimal

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.contrib.auth.models import User

from apps.user.models import UserProfileFund
from factories.model_factories import UserFactory, ProfileFactory, OrderFactory, OrderItemFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def user_profile(db, user):
    fund, _ = UserProfileFund.objects.get_or_create(value=Decimal("1.3"))
    return ProfileFactory(user=user, fund=fund)


@pytest.fixture
def order(db, user):
    order = OrderFactory(user=user)
    OrderItemFactory(order=order)
    OrderItemFactory(order=order)
    return order


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser('admin', 'admin@example.com', 'pass')


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def admin_site():
    return AdminSite()
