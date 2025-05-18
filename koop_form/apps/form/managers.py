from django.db import models

from apps.form.services import calculate_previous_weekday


previous_friday = calculate_previous_weekday()


class OrderManager(models.Manager):
    def filter_this_week_orders(self):
        return self.get_queryset().filter(date_created__gte=previous_friday)
