from django.urls import path
from . import views

app_name = 'user_portal'

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('access/', views.access_stocktake, name='access_stocktake'),
    path('stocktake/', views.stocktake_entry, name='stocktake_entry'),
    path('tables/', views.view_tables, name='view_tables'),
    path('tables/<int:table_id>/export/', views.export_table, name='export_table'),
    path('help/', views.help_page, name='help'),
]