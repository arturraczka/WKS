from apps.form.services import check_if_form_is_open
from django.contrib import messages


class FormOpenMixin:
    """Adds feature of blocking POST requests outside a time period declared in check_if_form_is_open() function.
    Mixin to be used only with views inheriting POST method from other CBV/Mixins"""
    def post(self, request, *args, **kwargs):
        if check_if_form_is_open():
            return super().post(request, *args, **kwargs)
        else:
            messages.warning(
                self.request,
                "Nie możesz już składać zamówień. Formularz zamyka się w poniedziałki o 20:00.",
            )
            form = self.get_form()
            return self.form_invalid(form)
