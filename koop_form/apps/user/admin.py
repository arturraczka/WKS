from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from import_export.admin import ImportExportModelAdmin
from import_export import resources

from apps.user.models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "userprofiles"


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        import_id_fields = ("phone_number",)
        fields = (
            "fund",
            "phone_number",
        )


class UserProfileAdmin(ImportExportModelAdmin):
    resource_classes = [UserProfileResource]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
