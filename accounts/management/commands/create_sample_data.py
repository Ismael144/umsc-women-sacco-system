from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Region, Sacco, ActivityLog
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing the admin system'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create regions
            regions_data = [
                {'name': 'Central Region', 'description': 'Central Uganda region'},
                {'name': 'Northern Region', 'description': 'Northern Uganda region'},
                {'name': 'Eastern Region', 'description': 'Eastern Uganda region'},
                {'name': 'Western Region', 'description': 'Western Uganda region'},
            ]
            
            regions = []
            for region_data in regions_data:
                region, created = Region.objects.get_or_create(
                    name=region_data['name'],
                    defaults={'description': region_data['description']}
                )
                regions.append(region)
                if created:
                    self.stdout.write(f'Created region: {region.name}')
            
            # Create system admin if doesn't exist
            system_admin, created = User.objects.get_or_create(
                username='system_admin',
                defaults={
                    'email': 'system@umsc.com',
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'is_system_admin': True,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                system_admin.set_password('admin123')
                system_admin.save()
                self.stdout.write('Created system admin: system_admin')
            
            # Create regional admins
            regional_admins_data = [
                {
                    'username': 'central_admin',
                    'email': 'central@umsc.com',
                    'first_name': 'Central',
                    'last_name': 'Admin',
                    'region': regions[0]
                },
                {
                    'username': 'northern_admin',
                    'email': 'northern@umsc.com',
                    'first_name': 'Northern',
                    'last_name': 'Admin',
                    'region': regions[1]
                },
                {
                    'username': 'eastern_admin',
                    'email': 'eastern@umsc.com',
                    'first_name': 'Eastern',
                    'last_name': 'Admin',
                    'region': regions[2]
                },
                {
                    'username': 'western_admin',
                    'email': 'western@umsc.com',
                    'first_name': 'Western',
                    'last_name': 'Admin',
                    'region': regions[3]
                },
            ]
            
            for admin_data in regional_admins_data:
                admin, created = User.objects.get_or_create(
                    username=admin_data['username'],
                    defaults={
                        'email': admin_data['email'],
                        'first_name': admin_data['first_name'],
                        'last_name': admin_data['last_name'],
                        'region': admin_data['region'],
                        'is_regional_admin': True,
                        'is_staff': True,
                    }
                )
                if created:
                    admin.set_password('admin123')
                    admin.save()
                    self.stdout.write(f'Created regional admin: {admin.username}')
            
            # Create sample Saccos
            saccos_data = [
                {
                    'name': 'Kampala Women Sacco',
                    'registration_number': 'KWS001',
                    'address': 'Kampala Central',
                    'phone': '+256700000001',
                    'email': 'info@kampalawomensacco.com',
                    'region': regions[0],
                    'created_by': system_admin
                },
                {
                    'name': 'Gulu Women Sacco',
                    'registration_number': 'GWS001',
                    'address': 'Gulu Town',
                    'phone': '+256700000002',
                    'email': 'info@guluwomensacco.com',
                    'region': regions[1],
                    'created_by': system_admin
                },
                {
                    'name': 'Jinja Women Sacco',
                    'registration_number': 'JWS001',
                    'address': 'Jinja Town',
                    'phone': '+256700000003',
                    'email': 'info@jinjawomensacco.com',
                    'region': regions[2],
                    'created_by': system_admin
                },
                {
                    'name': 'Mbarara Women Sacco',
                    'registration_number': 'MWS001',
                    'address': 'Mbarara Town',
                    'phone': '+256700000004',
                    'email': 'info@mbararawomensacco.com',
                    'region': regions[3],
                    'created_by': system_admin
                },
            ]
            
            for sacco_data in saccos_data:
                sacco, created = Sacco.objects.get_or_create(
                    registration_number=sacco_data['registration_number'],
                    defaults=sacco_data
                )
                if created:
                    self.stdout.write(f'Created Sacco: {sacco.name}')
                    
                    # Create Sacco admin
                    sacco_admin_username = f"{sacco.name.lower().replace(' ', '_')}_admin"
                    sacco_admin, created = User.objects.get_or_create(
                        username=sacco_admin_username,
                        defaults={
                            'email': f'admin@{sacco.name.lower().replace(" ", "")}.com',
                            'first_name': 'Sacco',
                            'last_name': 'Administrator',
                            'sacco': sacco,
                            'is_sacco_admin': True,
                            'is_staff': True,
                        }
                    )
                    if created:
                        sacco_admin.set_password('admin123')
                        sacco_admin.save()
                        self.stdout.write(f'Created Sacco admin: {sacco_admin.username}')
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created sample data!')
            )
            self.stdout.write('\nLogin credentials:')
            self.stdout.write('System Admin: system_admin / admin123')
            self.stdout.write('Regional Admins: central_admin, northern_admin, eastern_admin, western_admin / admin123')
            self.stdout.write('Sacco Admins: [sacco_name]_admin / admin123')