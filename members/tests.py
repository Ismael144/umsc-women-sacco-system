from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Member, MemberGroup, MemberProfile
from accounts.models import Sacco, Region

User = get_user_model()


class MemberModelTest(TestCase):
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

    def test_member_creation(self):
        member = Member.objects.create(
            sacco=self.sacco,
            member_number="MEM001",
            first_name="John",
            last_name="Doe",
            phone="1234567890",
            gender="Male",
            date_of_birth="1990-01-01",
            home_address="123 Test St",
            village_town="Test Town",
            district="Test District",
            date_joined="2023-01-01",
            created_by=self.user
        )
        self.assertEqual(member.full_name, "John Doe")
        self.assertEqual(member.sacco, self.sacco)
        self.assertEqual(member.status, "Active")

    def test_member_with_user_account(self):
        member = Member.objects.create(
            sacco=self.sacco,
            member_number="MEM002",
            first_name="Jane",
            last_name="Smith",
            phone="0987654321",
            gender="Female",
            date_of_birth="1992-05-15",
            home_address="456 Test Ave",
            village_town="Test City",
            district="Test District",
            date_joined="2023-01-01",
            user_account=self.user,
            created_by=self.user
        )
        self.assertEqual(member.user_account, self.user)

    def test_member_profile_creation(self):
        member = Member.objects.create(
            sacco=self.sacco,
            member_number="MEM003",
            first_name="Bob",
            last_name="Johnson",
            phone="5555555555",
            gender="Male",
            date_of_birth="1988-12-25",
            home_address="789 Test Blvd",
            village_town="Test Village",
            district="Test District",
            date_joined="2023-01-01",
            created_by=self.user
        )
        
        profile = MemberProfile.objects.create(
            member=member,
            next_of_kin_name="Alice Johnson",
            next_of_kin_phone="1111111111",
            relationship="Spouse",
            kyc_complete=True
        )
        self.assertEqual(profile.member, member)
        self.assertTrue(profile.kyc_complete)

    def test_member_group_creation(self):
        member1 = Member.objects.create(
            sacco=self.sacco,
            member_number="MEM004",
            first_name="Alice",
            last_name="Brown",
            phone="2222222222",
            gender="Female",
            date_of_birth="1995-03-10",
            home_address="321 Test Rd",
            village_town="Test Town",
            district="Test District",
            date_joined="2023-01-01",
            created_by=self.user
        )
        
        member2 = Member.objects.create(
            sacco=self.sacco,
            member_number="MEM005",
            first_name="Charlie",
            last_name="Wilson",
            phone="3333333333",
            gender="Male",
            date_of_birth="1993-07-20",
            home_address="654 Test Ln",
            village_town="Test City",
            district="Test District",
            date_joined="2023-01-01",
            created_by=self.user
        )
        
        group = MemberGroup.objects.create(
            sacco=self.sacco,
            name="Test Group",
            code="TG001",
            description="A test group",
            leader=member1
        )
        group.members.add(member1, member2)
        
        self.assertEqual(group.sacco, self.sacco)
        self.assertEqual(group.leader, member1)
        self.assertEqual(group.members.count(), 2)


class MemberViewsTest(TestCase):
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
        self.sacco_admin = User.objects.create_user(
            username="saccoadmin",
            email="saccoadmin@example.com",
            password="saccoadmin123",
            sacco=self.sacco,
            is_sacco_admin=True
        )
        self.member = Member.objects.create(
            sacco=self.sacco,
            member_number="MEM001",
            first_name="John",
            last_name="Doe",
            phone="1234567890",
            gender="Male",
            date_of_birth="1990-01-01",
            home_address="123 Test St",
            village_town="Test Town",
            district="Test District",
            date_joined="2023-01-01",
            created_by=self.sacco_admin
        )

    def test_member_list_view_requires_login(self):
        response = self.client.get(reverse('member_list'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('member_list')}")

    def test_member_list_view_authenticated(self):
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.get(reverse('member_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_member_list_view_search(self):
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.get(reverse('member_list'), {'search': 'John'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_member_list_view_status_filter(self):
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.get(reverse('member_list'), {'status': 'Active'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_register_member_view_get(self):
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.get(reverse('register_member'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Register Member")

    def test_register_member_view_post(self):
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.post(reverse('register_member'), {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '0987654321',
            'gender': 'Female',
            'date_of_birth': '1992-05-15',
            'home_address': '456 Test Ave',
            'village_town': 'Test City',
            'district': 'Test District',
            'next_of_kin_name': 'John Smith',
            'next_of_kin_phone': '1111111111',
            'relationship': 'Father'
        })
        self.assertRedirects(response, reverse('member_list'))
        self.assertTrue(Member.objects.filter(first_name='Jane').exists())

    def test_member_profile_view(self):
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.get(reverse('member_profile', args=[self.member.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")

    def test_member_groups_view(self):
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.get(reverse('member_groups'))
        self.assertEqual(response.status_code, 200)

    def test_member_groups_post(self):
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.post(reverse('member_groups'), {
            'name': 'New Group',
            'code': 'NG001',
            'description': 'A new test group',
            'meeting_frequency': 'Monthly',
            'social_fund_balance': '1000.00',
            'group_guarantee_limit': '5000.00'
        })
        self.assertRedirects(response, reverse('member_groups'))
        self.assertTrue(MemberGroup.objects.filter(name='New Group').exists())

    def test_inactive_members_view(self):
        # Create an inactive member
        inactive_member = Member.objects.create(
            sacco=self.sacco,
            member_number="MEM002",
            first_name="Inactive",
            last_name="Member",
            phone="5555555555",
            gender="Male",
            date_of_birth="1990-01-01",
            home_address="123 Test St",
            village_town="Test Town",
            district="Test District",
            date_joined="2023-01-01",
            status="Inactive",
            created_by=self.sacco_admin
        )
        
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.get(reverse('inactive_members'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inactive Member")

    def test_search_members_ajax(self):
        self.client.login(username="saccoadmin", password="saccoadmin123")
        response = self.client.get(reverse('search_members'), {'q': 'John'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data['members']) > 0)
        self.assertEqual(data['members'][0]['first_name'], 'John')

    def test_member_dashboard_view(self):
        # Create a member with user account
        member_user = User.objects.create_user(
            username="memberuser",
            email="member@example.com",
            password="member123",
            sacco=self.sacco
        )
        member = Member.objects.create(
            sacco=self.sacco,
            member_number="MEM003",
            first_name="Member",
            last_name="User",
            phone="6666666666",
            gender="Male",
            date_of_birth="1990-01-01",
            home_address="123 Test St",
            village_town="Test Town",
            district="Test District",
            date_joined="2023-01-01",
            user_account=member_user,
            created_by=self.sacco_admin
        )
        
        self.client.login(username="memberuser", password="member123")
        response = self.client.get(reverse('member_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Member User")