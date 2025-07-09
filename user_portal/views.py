from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from hod.models import Department, StocktakeTable, StocktakeRecord, StocktakeAccess
from django.views.decorators.http import require_POST
import pandas as pd
from io import BytesIO
from django.http import HttpResponse

def home(request):
    # Clear any previous stocktake session
    if 'current_stocktake_id' in request.session:
        del request.session['current_stocktake_id']
    
    if request.method == 'POST' and 'department' in request.POST:
        request.session['department'] = request.POST['department']
        return redirect('user_portal:home')
    
    department_code = request.session.get('department')
    department = Department.objects.get(code=department_code) if department_code else None
    
    # Get active tables if department exists
    active_tables = None
    if department:
        active_tables = StocktakeTable.objects.filter(
            department=department,
            is_active=True
        )
    
    context = {
        'department': department,
        'departments': Department.objects.all(),
        'active_tables': active_tables  # Pass the pre-filtered queryset
    }
    return render(request, 'user_portal/home.html', context)

def logout_view(request):
    request.session.flush()
    return redirect('user_portal:home')

def access_stocktake(request):
    if 'department' not in request.session:
        messages.error(request, 'Please select a department first')
        return redirect('user_portal:home')
    
    if request.method == 'POST':
        access_code = request.POST.get('access_code')
        try:
            stocktake = StocktakeTable.objects.get(
                access_code=access_code,
                department__code=request.session['department'],
                is_active=True
            )
            
            # Check for existing access
            existing_access = StocktakeAccess.objects.filter(
                session_key=request.session.session_key,
                stocktake_table=stocktake
            ).first()

            if existing_access is None:
                # Record access without requiring user login
                StocktakeAccess.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    stocktake_table=stocktake,
                    session_key=request.session.session_key
                )
            else:
                messages.info(request, 'You already have access to this stocktake.')

            request.session['current_stocktake_id'] = stocktake.id
            return redirect('user_portal:stocktake_entry')
        except StocktakeTable.DoesNotExist:
            messages.error(request, 'Invalid access code or the stocktake is not active')
    
    return render(request, 'user_portal/access_stocktake.html')

def stocktake_entry(request):
    if 'current_stocktake_id' not in request.session:
        return redirect('user_portal:access_stocktake')
    
    stocktake = get_object_or_404(StocktakeTable, id=request.session['current_stocktake_id'])
    records = StocktakeRecord.objects.filter(
        stocktake_table=stocktake
    ).select_related('drug').order_by('drug__name')
    
    if request.method == 'POST':
        # Process only the submitted record (single form per row)
        record_id = request.POST.get('record_id')
        if record_id:
            record = get_object_or_404(StocktakeRecord, id=record_id, stocktake_table=stocktake)
            
            if 'update' in request.POST:
                packs = request.POST.get('packs', '0')
                singles = request.POST.get('singles', '0')
                
                # Validate and convert inputs
                record.packs = int(packs) if packs.isdigit() and packs else 0
                record.singles = int(singles) if singles.isdigit() and singles else 0
                record.expiry_date = request.POST.get('expiry_date', None)
                record.save()
                messages.success(request, f'{record.drug.name} updated successfully!')
            
            elif 'add' in request.POST:
                packs = request.POST.get('packs', '0')
                singles = request.POST.get('singles', '0')
                
                # Validate and convert inputs
                record.packs += int(packs) if packs.isdigit() and packs else 0
                record.singles += int(singles) if singles.isdigit() and singles else 0
                if request.POST.get('expiry_date'):
                    record.expiry_date = request.POST.get('expiry_date')
                record.save()
                messages.success(request, f'Added to {record.drug.name} successfully!')
        
        return redirect('user_portal:stocktake_entry')
    
    # Calculate progress
    total_items = records.count()
    completed_items = records.exclude(packs=0, singles=0).count()
    progress_percent = int((completed_items / total_items) * 100) if total_items > 0 else 0
    
    context = {
        'stocktake': stocktake,
        'records': records,
        'progress_percent': progress_percent,
        'completed_items': completed_items,
        'total_items': total_items
    }
    return render(request, 'user_portal/stocktake_entry.html', context)

def view_tables(request):
    if 'department' not in request.session:
        messages.error(request, 'Please select a department first')
        return redirect('user_portal:home')
    
    department = get_object_or_404(Department, code=request.session['department'])
    tables = StocktakeTable.objects.filter(department=department).order_by('-created_at')
    
    selected_table_id = request.session.get('current_stocktake_id')
    selected_table = None
    records = []
    
    if request.method == 'POST' or selected_table_id:
        table_id = request.POST.get('table_id', selected_table_id)
        if table_id:
            selected_table = get_object_or_404(StocktakeTable, id=table_id, department=department)
            records = StocktakeRecord.objects.filter(
                stocktake_table=selected_table
            ).select_related('drug').order_by('drug__name')
    
    context = {
        'department': department,
        'tables': tables,
        'selected_table': selected_table,
        'records': records
    }
    return render(request, 'user_portal/view_tables.html', context)

def help_page(request):
    return render(request, 'user_portal/help.html')

def export_table(request, table_id):
    if 'department' not in request.session:
        return redirect('user_portal:home')
    
    table = get_object_or_404(StocktakeTable, id=table_id, department__code=request.session['department'])
    records = StocktakeRecord.objects.filter(stocktake_table=table).select_related('drug')
    
    # Create DataFrame
    data = []
    for record in records:
        data.append({
            'DRUG NAME': record.drug.name,
            'PACKS': record.packs,
            'SINGLES': record.singles,
            'EXPIRY DATE': record.expiry_date or '',
        })
    
    df = pd.DataFrame(data)
    
    # Determine format
    export_format = request.GET.get('format', 'excel')
    
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{table.name}_stocktake.csv"'
        df.to_csv(response, index=False)
    else:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Stocktake')
        
        response = HttpResponse(output.getvalue(), 
                             content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{table.name}_stocktake.xlsx"'
    
    return response