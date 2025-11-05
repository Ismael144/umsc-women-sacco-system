from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.management import call_command
from .models import Sacco, Region, ActivityLog
from members.models import Member

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name="Test Region")
        self.sacco = Sacco.objects.create(
            name="Test Sacco",
            registration_number="TEST001",
            address="Test Address",
            phone="1234567890",
            email="test@sacco.com",
            region=self.region
        )

    def test_user_creation(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            sacco=self.sacco
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.sacco, self.sacco)
        self.assertFalse(user.is_system_admin)
        self.assertFalse(user.is_sacco_admin)

    def test_system_admin_creation(self):
        user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_system_admin=True
        )
        self.assertTrue(user.is_system_admin)
        self.assertTrue(user.is_staff)

    def test_sacco_admin_creation(self):
        user = User.objects.create_user(
            username="saccoadmin",
            email="saccoadmin@example.com",
            password="saccoadmin123",
            sacco=self.sacco,
            is_sacco_admin=True
        )
        self.assertTrue(user.is_sacco_admin)
        self.assertEqual(user.sacco, self.sacco)


class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.region = Region.objects.create(name="Test Region")
        self.sacco = Sacco.objects.create(
            name="Test Sacco",
            registration_number="TEST001",
            address="Test Address",
            phone="1234567890",
            email="test@sacco.com",
            region=self.region
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            sacco=self.sacco
        )

    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login')

    def test_login_view_post_valid(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_view_post_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')

    def test_dashboard_redirect_system_admin(self):
        admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_system_admin=True
        )
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_dashboard_redirect_sacco_admin(self):
        sacco_admin = User.objects.create_user(
            username="saccoadmin",
            email="saccoadmin@example.com",
            password="saccoadmin123",
            sacco=self.sacco,
            is_sacco_admin=True
        )
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('sacco_admin_dashboard'))

    def test_logout_view(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


class SaccoManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.region = Region.objects.create(name="Test Region")
        self.system_admin = User.objects.create_user(
            username="systemadmin",
            email="systemadmin@example.com",
            password="systemadmin123",
            is_system_admin=True
        )

    def test_create_sacco_view_requires_admin(self):
        # Test without login
        response = self.client.get(reverse('create_sacco'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('create_sacco')}")

        # Test with regular user
        regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="regular123"
        )
        self.client.login(username="regular", password="regular123")
        response = self.client.get(reverse('create_sacco'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_create_sacco_view_system_admin(self):
        self.client.login(username="systemadmin", password="systemadmin123")
        response = self.client.get(reverse('create_sacco'))
        self.assertEqual(response.status_code, 200)

    def test_create_sacco_post(self):
        self.client.login(username="systemadmin", password="systemadmin123")
        response = self.client.post(reverse('create_sacco'), {
            'name': 'New Sacco',
            'registration_number': 'NEW001',
            'address': 'New Address',
            'phone': '9876543210',
            'email': 'new@sacco.com',
            'region': self.region.id,
            'admin_username': 'newsaccoadmin',
            'admin_email': 'newsaccoadmin@sacco.com',
            'admin_first_name': 'New',
            'admin_last_name': 'Admin',
            'admin_password': 'newsaccoadmin123',
            'admin_password_confirm': 'newsaccoadmin123'
        })
        self.assertRedirects(response, reverse('admin_dashboard'))
        self.assertTrue(Sacco.objects.filter(name='New Sacco').exists())


class ActivityLogTest(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name="Test Region")
        self.sacco = Sacco.objects.create(
            name="Test Sacco",
            registration_number="TEST001",
            address="Test Address",
            phone="1234567890",
            email="test@sacco.com",
            region=self.region
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            sacco=self.sacco
        )

    def test_activity_log_creation(self):
        from .utils import log_activity
        log_activity(
            user=self.user,
            action='create',
            model_name='TestModel',
            object_id=1,
            object_name='Test Object',
            description='Test activity'
        )
        self.assertTrue(ActivityLog.objects.filter(user=self.user).exists())

    def test_activity_log_with_sacco_region(self):
        from .utils import log_activity
        log_activity(
            user=self.user,
            action='create',
            model_name='TestModel',
            object_id=1,
            object_name='Test Object',
            description='Test activity',
            sacco=self.sacco,
            region=self.region
        )
        log = ActivityLog.objects.get(user=self.user)
        self.assertEqual(log.sacco, self.sacco)
        self.assertEqual(log.region, self.region)


class ManagementCommandTest(TestCase):
    def test_create_sample_data_command(self):
        call_command('create_sample_data')
        
        # Check if regions were created
        self.assertTrue(Region.objects.exists())
        
        # Check if system admin was created
        self.assertTrue(User.objects.filter(is_system_admin=True).exists())
        
        # Check if regional admins were created
        self.assertTrue(User.objects.filter(is_regional_admin=True).exists())
        
        # Check if saccos were created
        self.assertTrue(Sacco.objects.exists())