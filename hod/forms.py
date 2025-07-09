from django import forms
from django.core.validators import FileExtensionValidator
from .models import Department, Drug, StocktakeTable
import pandas as pd
import io

class ImportDrugsForm(forms.Form):
    department = forms.ModelChoiceField(queryset=Department.objects.all())
    excel_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'csv'])]
    )
    
    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            if 'DRUG NAME' not in df.columns:
                raise forms.ValidationError("Excel file must contain 'DRUG NAME' column")
            
            return df
        except Exception as e:
            raise forms.ValidationError(f"Error reading file: {str(e)}")

class DrugForm(forms.ModelForm):
    class Meta:
        model = Drug
        fields = ['name', 'department']

class StocktakeTableForm(forms.ModelForm):
    class Meta:
        model = StocktakeTable
        fields = ['name', 'department', 'access_code']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and not user.is_superuser and user.department:
            self.fields['department'].queryset = Department.objects.filter(id=user.department.id)
            self.fields['department'].initial = user.department
            self.fields['department'].disabled = True