from django.db.models import Prefetch
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
import logging
from apps.form.models import Order, OrderItem

logger = logging.getLogger("django.server")


class Command(BaseCommand):
    help = "Sends this week's order summary to users that allows receiving emails"

    def handle(self, *args, **options):
        orders_qs = (
            Order.objects.filter_this_week_orders()
            .select_related("user__userprofile__fund")
            .prefetch_related(
                "products",
                Prefetch(
                    "orderitems", queryset=OrderItem.objects.select_related("product")
                ),
            )
        )
        for order in orders_qs:
            if not hasattr(order.user, "userprofile"):
                continue
            if not order.user.userprofile.allow_emails:
                continue
            text_content = render_to_string(
                "user/emails/order_summary.txt",
                context={"order": order},
            )
            subject = "Podsumowanie zamówienia " + now().strftime("%d.%m")

            email = EmailMessage(
                subject=subject,
                body=text_content,
                to=[
                    order.user.email,
                ],
            )
            email.send(fail_silently=True)
