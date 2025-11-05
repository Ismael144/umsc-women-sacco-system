from django.db import models
from accounts.models import Sacco
from members.models import Member


class SavingProduct(models.Model):
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    product_code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    minimum_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    max_balance = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_term_product = models.BooleanField(default=False)
    term_months = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class SavingsAccount(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Frozen', 'Frozen'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    product = models.ForeignKey(SavingProduct, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=50, unique=True)
    opened_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    interest_accrued = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    mature_date = models.DateField(null=True, blank=True)
    receive_via_mobile_money = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.member.full_name} - {self.product.name}"


class SavingsTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal'),
        ('Interest', 'Interest'),
        ('Fee', 'Fee'),
        ('Transfer', 'Transfer'),
    ]
    
    account = models.ForeignKey(SavingsAccount, on_delete=models.CASCADE, related_name='transactions')
    txn_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    running_balance = models.DecimalField(max_digits=14, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    narration = models.TextField(blank=True)
    mobile_money_tx_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    performed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='performed_savings_transactions')
    performed_at = models.DateTimeField(auto_now_add=True)
    related_document = models.ForeignKey('members.Document', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.account} - {self.txn_type} - {self.amount}"