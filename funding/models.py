from django.db import models
from accounts.models import Sacco


class FundingSource(models.Model):
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Funding(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('allocated', 'Allocated'),
        ('spent', 'Spent'),
    ]
    
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE)
    source = models.ForeignKey(FundingSource, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    received_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.source.name} - {self.amount}"


class FundsAllocation(models.Model):
    funding = models.ForeignKey(Funding, on_delete=models.CASCADE)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    allocated_date = models.DateTimeField(auto_now_add=True)
    allocated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.funding} - {self.allocated_amount}"


class ExpenditureLog(models.Model):
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    category = models.CharField(max_length=100)
    expenditure_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.description} - {self.amount}"