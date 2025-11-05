from django.db import models
from django.utils import timezone
from accounts.models import Sacco
from members.models import Member
import uuid


class LoanProduct(models.Model):
    INTEREST_TYPE_CHOICES = [
        ('Flat', 'Flat Rate'),
        ('Reducing', 'Reducing Balance'),
    ]
    
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    product_code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    interest_type = models.CharField(max_length=20, choices=INTEREST_TYPE_CHOICES, default='Reducing')
    processing_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_amount = models.DecimalField(max_digits=14, decimal_places=2)
    min_amount = models.DecimalField(max_digits=14, decimal_places=2)
    max_duration_months = models.IntegerField()
    min_duration_months = models.IntegerField()
    grace_period_months = models.IntegerField(default=0)
    allow_partial_disbursement = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Loan(models.Model):
    STATUS_CHOICES = [
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('pending_disbursement', 'Pending Disbursement'),
        ('disbursed', 'Disbursed'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('declined', 'Declined'),
        ('withdrawn', 'Withdrawn'),
        ('written_off', 'Written Off'),
        ('defaulted', 'Defaulted'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    product = models.ForeignKey(LoanProduct, on_delete=models.CASCADE)
    loan_ref = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Human-friendly loan reference")
    loan_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    amount_requested = models.DecimalField(max_digits=14, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    amount_disbursed = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    principal = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    interest_type = models.CharField(max_length=20, choices=LoanProduct.INTEREST_TYPE_CHOICES, default='Reducing')
    duration_months = models.IntegerField()
    tenure_months = models.IntegerField(null=True, blank=True)
    monthly_payment = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    installment_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    outstanding_principal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    outstanding_interest = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval')
    purpose = models.TextField()
    collateral = models.TextField(blank=True)
    guarantors = models.TextField(blank=True)
    repayment_schedule = models.JSONField(blank=True, null=True, help_text="Amortization schedule")
    repay_via_mobile_money = models.BooleanField(default=False)
    application_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    disbursement_date = models.DateTimeField(null=True, blank=True)
    disbursed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='disbursed_loans')
    maturity_date = models.DateTimeField(null=True, blank=True)
    written_off_at = models.DateTimeField(null=True, blank=True)
    written_off_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='written_off_loans')
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='closed_loans')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.loan_number:
            # Generate loan number: SACCO-YYYY-XXXXX
            year = timezone.now().year
            last_loan = Loan.objects.filter(
                loan_number__startswith=f"{self.member.sacco.name.upper()}-{year}-"
            ).order_by('-loan_number').first()
            
            if last_loan and last_loan.loan_number:
                try:
                    last_number = int(last_loan.loan_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.loan_number = f"{self.member.sacco.name.upper()}-{year}-{new_number:05d}"
        
        if not self.loan_ref:
            # Generate human-friendly reference with timestamp to ensure uniqueness
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.loan_ref = f"LOAN-{self.member.member_number}-{timestamp}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.member.full_name} - {self.loan_number}"
    
    @property
    def total_interest(self):
        amount = self.amount_approved or self.amount_requested
        if amount:
            return (amount * self.interest_rate * self.duration_months) / (12 * 100)
        return 0
    
    @property
    def total_amount(self):
        amount = self.amount_approved or self.amount_requested
        if amount:
            return amount + self.total_interest
        return 0
    
    @property
    def total_repayments(self):
        """Calculate total amount repaid"""
        return self.repayments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    @property
    def remaining_balance(self):
        """Calculate remaining balance to be paid"""
        return max(0, self.total_amount - self.total_repayments)
    
    @property
    def is_fully_repaid(self):
        """Check if loan is fully repaid"""
        return self.remaining_balance <= 0 and self.status in ['active', 'disbursed']
    
    def mark_as_closed(self, closed_by=None):
        """Mark loan as closed when fully repaid"""
        if self.is_fully_repaid:
            self.status = 'closed'
            self.closed_at = timezone.now()
            if closed_by:
                self.closed_by = closed_by
            self.save()
            return True
        return False


class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    applied_to_principal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    applied_to_interest = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    applied_to_fees = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, default='Cash')
    reference_number = models.CharField(max_length=100, blank=True)
    mobile_money_tx_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    running_outstanding_principal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    received_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='received_repayments')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.loan} - {self.amount}"


class LoanCollateral(models.Model):
    """Collateral and security information for loans"""
    COLLATERAL_TYPE_CHOICES = [
        ('GroupGuarantee', 'Group Guarantee'),
        ('MovableAsset', 'Movable Asset'),
        ('TitleDeed', 'Title Deed'),
        ('Vehicle', 'Vehicle'),
        ('Other', 'Other')
    ]
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='collaterals')
    collateral_type = models.CharField(max_length=20, choices=COLLATERAL_TYPE_CHOICES)
    description = models.TextField()
    value = models.DecimalField(max_digits=14, decimal_places=2)
    guarantor_group = models.ForeignKey('members.MemberGroup', on_delete=models.SET_NULL, null=True, blank=True)
    legal_document = models.ForeignKey('members.Document', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Loan Collateral"
        verbose_name_plural = "Loan Collaterals"
    
    def __str__(self):
        return f"{self.loan} - {self.collateral_type}"


class LoanCharge(models.Model):
    """Fees and penalties for loans"""
    CHARGE_TYPE_CHOICES = [
        ('ProcessingFee', 'Processing Fee'),
        ('LatePenalty', 'Late Payment Penalty'),
        ('Insurance', 'Insurance'),
        ('Other', 'Other')
    ]
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='charges')
    charge_type = models.CharField(max_length=20, choices=CHARGE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    charged_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Loan Charge"
        verbose_name_plural = "Loan Charges"
    
    def __str__(self):
        return f"{self.loan} - {self.charge_type} - {self.amount}"