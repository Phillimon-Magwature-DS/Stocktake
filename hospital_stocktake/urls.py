from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('hod/', include('hod.urls')),
    path('staff/', include('user_portal.urls')),
]