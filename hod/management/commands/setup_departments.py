from django.core.management.base import BaseCommand
from hod.models import Department

DEPARTMENTS = [
    {"name": "Emergency Room", "code": "ER", "icon": "fa-ambulance"},
    {"name": "Admission", "code": "ADMISSION", "icon": "fa-user-plus"},
    {"name": "Maternity", "code": "MATERNITY", "icon": "fa-baby"},
    {"name": "Theatre", "code": "THEATRE", "icon": "fa-theater-masks"},
    {"name": "Laboratory", "code": "LAB", "icon": "fa-flask"},
    {"name": "Radiology", "code": "RADIOLOGY", "icon": "fa-x-ray"},
    {"name": "Dentist", "code": "DENTIST", "icon": "fa-tooth"},
    {"name": "Pharmacy Dispensary", "code": "PHARM_DISP", "icon": "fa-pills"},
    {"name": "Pharmacy Hospital", "code": "PHARM_HOSP", "icon": "fa-hospital"},
    {"name": "Super Admin", "code": "SUPER_ADMIN", "icon": "fa-user-shield"},
]

class Command(BaseCommand):
    help = 'Creates initial departments'
    
    def handle(self, *args, **options):
        for dept in DEPARTMENTS:
            department, created = Department.objects.get_or_create(
                name=dept['name'],
                code=dept['code'],
                defaults={'icon': dept['icon']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created department: {dept['name']} with icon: {dept['icon']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Department already exists: {dept['name']}"))