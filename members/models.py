from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import Sacco
import uuid

User = get_user_model()


class Member(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Widow', 'Widow'),
        ('Divorced', 'Divorced'),
    ]
    MEMBERSHIP_TYPE_CHOICES = [
        ('Individual', 'Individual'),
        ('Group', 'Group / Association'),
    ]
    MEMBERSHIP_CATEGORY_CHOICES = [
        ('Ordinary', 'Ordinary Member'),
        ('Associate', 'Associate Member'),
        ('Founding', 'Founding Member'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('MobileMoney', 'Mobile Money'),
        ('Bank', 'Bank Deposit'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
        ('Prospect', 'Prospect'),
    ]
    
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE)
    user_account = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    member_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20)
    national_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    passport_number = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    date_of_birth = models.DateField()
    home_address = models.TextField()
    village_town = models.CharField(max_length=100)
    district = models.CharField(max_length=50)
    subcounty = models.CharField(max_length=50, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    employer_name = models.CharField(max_length=200, blank=True, null=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # Membership info from UMSC women form
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_TYPE_CHOICES, null=True, blank=True)
    membership_category = models.CharField(max_length=20, choices=MEMBERSHIP_CATEGORY_CHOICES, null=True, blank=True)
    referred_by = models.CharField(max_length=200, null=True, blank=True)
    preferred_payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    monthly_contribution_commitment = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    group = models.ForeignKey('MemberGroup', on_delete=models.SET_NULL, null=True, blank=True)
    date_joined = models.DateField()
    shares_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    savings_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='members/photos/', blank=True, null=True)
    # Additional fields for comprehensive member data
    business_registration_status = models.CharField(max_length=20, choices=[
        ('Registered', 'Registered'),
        ('Informal', 'Informal'),
        ('None', 'None')
    ], default='Informal')
    autonomy_score = models.IntegerField(default=5, help_text="Score 0-10 for member autonomy/empowerment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_members')
    # Official use only fields
    application_received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications_received')
    application_received_designation = models.CharField(max_length=100, null=True, blank=True)
    application_received_at = models.DateField(null=True, blank=True)
    approved_by_committee = models.CharField(max_length=200, null=True, blank=True)
    approval_remarks = models.TextField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    # Attachments
    attachment_id_copy = models.FileField(upload_to='members/attachments/', null=True, blank=True)
    attachment_passport_photo = models.ImageField(upload_to='members/attachments/', null=True, blank=True)
    attachment_proof_initial_deposit = models.FileField(upload_to='members/attachments/', null=True, blank=True)
    attachment_recommendation_letter = models.FileField(upload_to='members/attachments/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.member_number})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class MemberProfile(models.Model):
    """Detailed member profile information"""
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='profile')
    next_of_kin_name = models.CharField(max_length=100, blank=True, null=True)
    next_of_kin_phone = models.CharField(max_length=20, blank=True, null=True)
    relationship = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number = models.CharField(max_length=20, blank=True, null=True)
    bank_branch = models.CharField(max_length=100, blank=True, null=True)
    kyc_complete = models.BooleanField(default=False)
    additional_documents = models.JSONField(blank=True, null=True)
    # Additional empowerment and social metrics
    business_type = models.CharField(max_length=100, blank=True, null=True)
    business_location = models.CharField(max_length=200, blank=True, null=True)
    years_in_business = models.IntegerField(null=True, blank=True)
    monthly_business_income = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    family_size = models.IntegerField(default=1)
    education_level = models.CharField(max_length=50, choices=[
        ('None', 'None'),
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
        ('Tertiary', 'Tertiary'),
        ('University', 'University')
    ], default='Primary')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Member Profile"
        verbose_name_plural = "Member Profiles"
    
    def __str__(self):
        return f"{self.member.full_name} Profile"


class MemberGroup(models.Model):
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)
    leader = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_groups')
    members = models.ManyToManyField(Member, blank=True, related_name='member_groups')
    # Additional group management fields
    meeting_frequency = models.CharField(max_length=20, choices=[
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly')
    ], default='Monthly')
    social_fund_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    group_guarantee_limit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Member Group"
        verbose_name_plural = "Member Groups"
    
    def __str__(self):
        return self.name


class MemberMobileWallet(models.Model):
    """Mobile money wallet information for members"""
    PROVIDER_CHOICES = [
        ('MTN', 'MTN Mobile Money'),
        ('Airtel', 'Airtel Money'),
        ('Equity', 'Equity Bank'),
        ('Other', 'Other')
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='mobile_wallets')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    phone_number = models.CharField(max_length=15, unique=True)
    is_primary = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Member Mobile Wallet"
        verbose_name_plural = "Member Mobile Wallets"
        unique_together = ['member', 'provider']
    
    def __str__(self):
        return f"{self.member.full_name} - {self.provider} ({self.phone_number})"


class Document(models.Model):
    """Document storage for KYC, receipts, and other attachments"""
    FILE_TYPE_CHOICES = [
        ('ID', 'National ID'),
        ('Passport', 'Passport'),
        ('Receipt', 'Receipt'),
        ('Contract', 'Contract'),
        ('Other', 'Other')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
    
    def __str__(self):
        return f"{self.file_type} - {self.uploaded_at}"


class AuditLog(models.Model):
    """Audit trail for all critical system activities"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.actor} - {self.action} - {self.timestamp}"


class Notification(models.Model):
    """System notifications and alerts"""
    CHANNEL_CHOICES = [
        ('Email', 'Email'),
        ('SMS', 'SMS'),
        ('InApp', 'In-App'),
        ('Push', 'Push Notification')
    ]
    
    ACTION_TYPE_CHOICES = [
        ('loan_approval', 'Loan Approval'),
        ('loan_rejection', 'Loan Rejection'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('savings_deposit', 'Savings Deposit'),
        ('savings_withdrawal', 'Savings Withdrawal'),
        ('member_registration', 'Member Registration'),
        ('payment_reminder', 'Payment Reminder'),
        ('password_reset', 'Password Reset'),
        ('system_alert', 'System Alert'),
        ('group_contribution', 'Group Contribution'),
        ('emergency_loan', 'Emergency Loan'),
        ('training_completion', 'Training Completion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='member_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='InApp')
    priority = models.CharField(max_length=20, choices=[
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical')
    ], default='Medium')
    
    # New fields for enhanced functionality
    action_type = models.CharField(max_length=30, choices=ACTION_TYPE_CHOICES, null=True, blank=True)
    action_url = models.URLField(max_length=500, null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['action_type']),
            models.Index(fields=['sent_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])