from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class Department(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True)
    icon = models.CharField(max_length=30, default='fa-building') 
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_hod = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.username} ({self.department.name if self.department else 'No Dept'})"

class Drug(models.Model):
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('name', 'department')
    
    def __str__(self):
        return f"{self.name} ({self.department})"

class StocktakeTable(models.Model):
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    access_code = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.department})"

class StocktakeRecord(models.Model):
    stocktake_table = models.ForeignKey(StocktakeTable, on_delete=models.CASCADE)
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE)
    packs = models.IntegerField(default=0)
    singles = models.IntegerField(default=0)
    expiry_date = models.CharField(max_length=20, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('stocktake_table', 'drug')
    
    def __str__(self):
        return f"{self.drug.name} in {self.stocktake_table.name}"

class StocktakeAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    stocktake_table = models.ForeignKey(StocktakeTable, on_delete=models.CASCADE)
    accessed_at = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40, blank=True) 
    
    class Meta:
        unique_together = (('user', 'stocktake_table'), ('session_key', 'stocktake_table'))