from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Sacco
from django.utils.crypto import get_random_string

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up the system with sample data'

    def handle(self, *args, **options):
        # Create System Admin
        if not User.objects.filter(is_system_admin=True).exists():
            system_admin = User.objects.create_user(
                username='system_admin',
                email='admin@system.com',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                is_system_admin=True,
                is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS('System Admin created:')
            )
            self.stdout.write(f'Username: system_admin')
            self.stdout.write(f'Password: admin123')
            self.stdout.write('')

        # Create Sample Sacco
        if not Sacco.objects.filter(name='UMSC Women Sacco').exists():
            sacco = Sacco.objects.create(
                name='UMSC Women Sacco',
                registration_number='REG001',
                address='123 Main Street, Kampala, Uganda',
                phone='+256 700 123 456',
                email='info@umsc-sacco.com',
                is_active=True
            )
            
            # Create Sacco Admin
            sacco_admin = User.objects.create_user(
                username='sacco_admin',
                email='admin@umsc-sacco.com',
                password='sacco123',
                first_name='Sacco',
                last_name='Administrator',
                sacco=sacco,
                is_sacco_admin=True,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS('Sample Sacco created:')
            )
            self.stdout.write(f'Sacco: {sacco.name}')
            self.stdout.write(f'Admin Username: sacco_admin')
            self.stdout.write(f'Admin Password: sacco123')
            self.stdout.write('')

        # Create Sample Member
        if not User.objects.filter(username='member001').exists():
            member_user = User.objects.create_user(
                username='member001',
                email='member@umsc-sacco.com',
                password='member123',
                first_name='John',
                last_name='Doe',
                sacco=sacco,
                is_active=True
            )
            
            # Create Member record
            from members.models import Member
            member = Member.objects.create(
                user_account=member_user,
                sacco=sacco,
                member_number='MEM0001',
                first_name='John',
                last_name='Doe',
                email='member@umsc-sacco.com',
                phone='+256 700 123 457',
                id_number='1234567890',
                gender='M',
                date_of_birth='1990-01-01',
                address='456 Member Street, Kampala',
                occupation='Teacher',
                monthly_income=500000,
                status='active'
            )
            
            self.stdout.write(
                self.style.SUCCESS('Sample Member created:')
            )
            self.stdout.write(f'Member Username: member001')
            self.stdout.write(f'Member Password: member123')
            self.stdout.write('')

        self.stdout.write(
            self.style.SUCCESS('System setup complete!')
        )
        self.stdout.write('')
        self.stdout.write('Login Credentials:')
        self.stdout.write('==================')
        self.stdout.write('System Admin:')
        self.stdout.write('  Username: system_admin')
        self.stdout.write('  Password: admin123')
        self.stdout.write('')
        self.stdout.write('Sacco Admin:')
        self.stdout.write('  Username: sacco_admin')
        self.stdout.write('  Password: sacco123')
        self.stdout.write('')
        self.stdout.write('Member:')
        self.stdout.write('  Username: member001')
        self.stdout.write('  Password: member123')

