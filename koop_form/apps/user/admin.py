from django.contrib import admin
from django.contrib.auth.models import User

from import_export.admin import ImportExportModelAdmin
from import_export import resources

from apps.form.admin import OrderInLine
from apps.user.models import UserProfile
from apps.user.models import UserProfileFund


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "userprofiles"


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        import_id_fields = ("email",)
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "id",
            "is_active",
        )


class UserAdmin(ImportExportModelAdmin):
    resource_classes = [UserResource]
    inlines = [UserProfileInline, OrderInLine]
    list_display = ["last_name", "first_name", "email", "is_active", "is_staff"]
    list_editable = []
    search_fields = [
        "last_name",
        "email",
    ]


class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        import_id_fields = ("user",)
        fields = (
            "fund",
            "phone_number",
            "user",
            "koop_id",
            "payment_balance",
        )


class UserProfileAdmin(ImportExportModelAdmin):
    resource_classes = [UserProfileResource]
    search_fields = [
        "user__last_name",
    ]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)


@admin.register(UserProfileFund)
class UserProfileFundAdmin(admin.ModelAdmin):
    pass
