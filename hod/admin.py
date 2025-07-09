from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Department, User, Drug, StocktakeTable, StocktakeRecord

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'department', 'is_hod', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Hospital Information', {'fields': ('department', 'is_hod')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Hospital Information', {'fields': ('department', 'is_hod')}),
    )

admin.site.register(Department)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Drug)
admin.site.register(StocktakeTable)
admin.site.register(StocktakeRecord)