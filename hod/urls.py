from django.urls import path
from . import views

app_name = 'hod'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home, name='home'),
    
    # Drug management
    path('drugs/import/', views.import_drugs, name='import_drugs'),
    path('drugs/', views.drug_database, name='drug_database'),
    path('drugs/<int:drug_id>/delete/', views.delete_drug, name='delete_drug'),
    
    # Stocktake tables
    path('stocktakes/new/', views.new_stocktake, name='new_stocktake'),
    path('stocktakes/', views.stocktake_tables, name='stocktake_tables'),
    path('stocktakes/<int:table_id>/delete/', views.delete_stocktake, name='delete_stocktake'),
    path('stocktakes/<int:table_id>/export/', views.export_stocktake, name='export_stocktake'),

    path('reports/', views.reports, name='reports'),
    path('reports/visualization/', views.report_visualization, name='report_visualization'),
    path('reports/visualization/<int:table_id>/', views.report_visualization, name='report_visualization'),
    path('instructions/', views.instructions, name='instructions'),
]