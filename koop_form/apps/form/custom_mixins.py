from apps.form.services import check_if_form_is_open
from django.contrib import messages


class FormOpenMixin:
    """Adds feature of blocking POST requests outside a time period declared in check_if_form_is_open() function.
    Mixin to be used only with views inheriting POST method from other CBV/Mixins"""

    def post(self, request, *args, **kwargs):
        self.object = None
        if check_if_form_is_open():
            return super().post(request, *args, **kwargs)
        else:
            messages.warning(
                self.request,
                "Zamówienia można składać od soboty od 12:00 do poniedziałku do 20:00.",
            )
            form = self.get_form()
            return self.form_invalid(form)
