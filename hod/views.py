from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db import transaction
import pandas as pd
import io
import random
import string
from .models import Department, Drug, StocktakeTable, StocktakeRecord, User
from .forms import ImportDrugsForm, DrugForm, StocktakeTableForm


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Hardcoded authentication - we'll replace with database later
        valid_logins = {
            'er_admin': ('ER', 'er_password123'),
            'admission_admin': ('ADMISSION', 'admission_password123'),
            'martenity_admin': ('MARTENITY', 'martenity_password123'),
            'theatre_admin': ('THEATRE', 'theatre_password123'),
            'lab_admin': ('LAB', 'lab_password123'),
            'radiology_admin': ('RADIOLOGY', 'radiology_password123'),
            'dentist_admin': ('DENTIST', 'dentist_password123'),
            'pharmacy_dispensary_admin': ('PHARM_DISP', 'dispensary_password123'),
            'pharmacy_hospital_admin': ('PHARM_HOSP', 'hospital_password123'),
            'super_admin': ('SUPER_ADMIN', 'super_password123'),
        }
        
        if username in valid_logins and password == valid_logins[username][1]:
            # Get or create user using your custom User model
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'is_hod': True,
                    'department': Department.objects.get(code=valid_logins[username][0])
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
            
            # Authenticate and login
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                request.session['department'] = valid_logins[username][0]
                request.session['is_superuser'] = (username == 'super_admin')
                next_url = request.GET.get('next', '/hod/home/')
                return redirect(next_url)
            else:
                messages.error(request, 'Authentication failed')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'hod/login.html')

def logout_view(request):
    logout(request)
    return redirect('hod:login')

@login_required
def home(request):
    # Get the department from session or user object
    department_code = request.session.get('department')
    if not department_code and hasattr(request.user, 'department'):
        department_code = request.user.department.code
        request.session['department'] = department_code
    
    # Get counts for dashboard
    try:
        department = Department.objects.get(code=department_code)
        drug_count = Drug.objects.filter(department=department).count()
        active_stocktakes = StocktakeTable.objects.filter(
            department=department, 
            is_active=True
        ).count()
    except (Department.DoesNotExist, AttributeError):
        drug_count = 0
        active_stocktakes = 0
        department = None
    
    context = {
        'drug_count': drug_count,
        'active_stocktakes': active_stocktakes,
        'recent_stocktakes': StocktakeTable.objects.filter(
            department=department
        ).order_by('-created_at')[:5] if department else [],
        'user': request.user
    }
    return render(request, 'hod/home.html', context)



@login_required
def import_drugs(request):
    if request.method == 'POST':
        form = ImportDrugsForm(request.POST, request.FILES)
        if form.is_valid():
            department = form.cleaned_data['department']
            df = form.cleaned_data['excel_file']
            
            try:
                with transaction.atomic():
                    # Delete existing drugs for this department if any
                    Drug.objects.filter(department=department).delete()
                    
                    # Get unique drug names
                    drug_names = df['DRUG NAME'].dropna().unique()
                    
                    # Create new drugs
                    drugs = [Drug(name=name, department=department) for name in drug_names]
                    Drug.objects.bulk_create(drugs)
                    
                    messages.success(request, f"Successfully imported {len(drug_names)} drugs for {department.name}")
                    return redirect('hod:drug_database')
            
            except Exception as e:
                messages.error(request, f"Error importing drugs: {str(e)}")
    else:
        form = ImportDrugsForm()
    
    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'hod/import_drugs.html', context)

@login_required
def drug_database(request):
    drugs = Drug.objects.filter(department=request.user.department).order_by('name')
    
    if request.method == 'POST':
        form = DrugForm(request.POST)
        if form.is_valid():
            drug = form.save(commit=False)
            drug.department = request.user.department
            drug.save()
            messages.success(request, "Drug added successfully!")
            return redirect('hod:drug_database')
    else:
        form = DrugForm()
    
    context = {
        'drugs': drugs,
        'form': form,
        'user': request.user
    }
    return render(request, 'hod/drug_database.html', context)

@login_required
def delete_drug(request, drug_id):
    drug = get_object_or_404(Drug, id=drug_id, department=request.user.department)
    drug.delete()
    messages.success(request, "Drug deleted successfully!")
    return redirect('hod:drug_database')

@login_required
def new_stocktake(request):
    if request.method == 'POST':
        form = StocktakeTableForm(request.POST, user=request.user)
        if form.is_valid():
            stocktake_table = form.save(commit=False)
            stocktake_table.created_by = request.user
            stocktake_table.save()
            
            # Create records for all drugs in this department
            drugs = Drug.objects.filter(department=stocktake_table.department)
            records = [
                StocktakeRecord(stocktake_table=stocktake_table, drug=drug)
                for drug in drugs
            ]
            StocktakeRecord.objects.bulk_create(records)
            
            messages.success(request, f"Stocktake table '{stocktake_table.name}' created successfully!")
            return redirect('hod:stocktake_tables')
    else:
        initial = {}
        if request.GET.get('generate_code'):
            initial['access_code'] = generate_access_code()
        form = StocktakeTableForm(user=request.user, initial=initial)
    
    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'hod/new_stocktake.html', context)

def generate_access_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@login_required
def stocktake_tables(request):
    tables = StocktakeTable.objects.filter(department=request.user.department).order_by('-created_at')
    
    context = {
        'tables': tables,
        'user': request.user
    }
    return render(request, 'hod/stocktake_tables.html', context)

@login_required
def delete_stocktake(request, table_id):
    table = get_object_or_404(StocktakeTable, id=table_id, department=request.user.department)
    table.delete()
    messages.success(request, "Stocktake table deleted successfully!")
    return redirect('hod:stocktake_tables')

@login_required
def export_stocktake(request, table_id):
    table = get_object_or_404(StocktakeTable, id=table_id, department=request.user.department)
    records = StocktakeRecord.objects.filter(stocktake_table=table).select_related('drug')
    
    # Create DataFrame
    data = []
    for record in records:
        data.append({
            'DRUG NAME': record.drug.name,
            'PACKS': record.packs,
            'SINGLES': record.singles,
            'EXPIRY DATE': record.expiry_date or '',
            'LAST UPDATED': record.last_updated.strftime('%Y-%m-%d %H:%M')
        })
    
    df = pd.DataFrame(data)
    
    # Determine format
    export_format = request.GET.get('format', 'excel')
    
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{table.name}_stocktake.csv"'
        df.to_csv(response, index=False)
    else:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Stocktake')
        
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{table.name}_stocktake.xlsx"'
    
    return response


@login_required
def reports(request):
    tables = StocktakeTable.objects.filter(
        department=request.user.department
    ).order_by('-created_at')
    
    context = {
        'tables': tables,
        'drugs': Drug.objects.filter(department=request.user.department)
    }
    return render(request, 'hod/reports.html', context)

@login_required
def report_visualization(request, table_id=None):
    table = get_object_or_404(StocktakeTable, id=table_id, department=request.user.department)
    records = StocktakeRecord.objects.filter(
        stocktake_table=table
    ).select_related('drug').order_by('drug__name')
    
    context = {
        'table': table,
        'records': records,
        'user': request.user
    }
    return render(request, 'hod/report_visualization.html', context)

def instructions(request):
    return render(request, 'hod/instructions.html')