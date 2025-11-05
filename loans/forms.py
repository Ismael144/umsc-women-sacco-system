from django import forms
from .models import Loan, LoanProduct, LoanRepayment


class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = [
            'member', 'product', 'amount_requested', 'principal', 'interest_rate', 'interest_type',
            'duration_months', 'tenure_months', 'monthly_payment', 'installment_amount',
            'purpose', 'collateral', 'guarantors', 'repay_via_mobile_money'
        ]
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'product': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter loan amount', 'step': '0.01', 'required': True}),
            'principal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter principal amount', 'step': '0.01'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter interest rate', 'step': '0.01', 'required': True}),
            'interest_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter duration in months', 'required': True}),
            'tenure_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter tenure in months'}),
            'monthly_payment': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter monthly payment', 'step': '0.01'}),
            'installment_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter installment amount', 'step': '0.01'}),
            'purpose': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter purpose of the loan', 'required': True}),
            'collateral': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter collateral details (optional)'}),
            'guarantors': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter guarantor details (optional)'}),
            'repay_via_mobile_money': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        amount_requested = cleaned_data.get('amount_requested')
        product = cleaned_data.get('product')
        duration_months = cleaned_data.get('duration_months')
        
        if product and amount_requested:
            if amount_requested < product.min_amount:
                raise forms.ValidationError(f'Loan amount must be at least {product.min_amount}')
            if amount_requested > product.max_amount:
                raise forms.ValidationError(f'Loan amount cannot exceed {product.max_amount}')
        
        if product and duration_months:
            if duration_months < product.min_duration_months:
                raise forms.ValidationError(f'Duration must be at least {product.min_duration_months} months')
            if duration_months > product.max_duration_months:
                raise forms.ValidationError(f'Duration cannot exceed {product.max_duration_months} months')
        
        return cleaned_data


class LoanProductForm(forms.ModelForm):
    class Meta:
        model = LoanProduct
        fields = [
            'name', 'product_code', 'description', 'interest_rate', 'interest_type',
            'max_amount', 'min_amount', 'max_duration_months', 'min_duration_months',
            'processing_fee_percent', 'grace_period_months', 'allow_partial_disbursement', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product code'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter product description'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'interest_type': forms.Select(attrs={'class': 'form-select'}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'max_duration_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter maximum duration'}),
            'min_duration_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter minimum duration'}),
            'processing_fee_percent': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'grace_period_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter grace period'}),
            'allow_partial_disbursement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        min_duration = cleaned_data.get('min_duration_months')
        max_duration = cleaned_data.get('max_duration_months')
        
        if min_amount and max_amount and min_amount >= max_amount:
            raise forms.ValidationError('Minimum amount must be less than maximum amount')
        
        if min_duration and max_duration and min_duration >= max_duration:
            raise forms.ValidationError('Minimum duration must be less than maximum duration')
        
        return cleaned_data
    
    def clean_product_code(self):
        product_code = self.cleaned_data.get('product_code')
        if product_code:
            # Get sacco from the form data or user's sacco
            sacco = self.cleaned_data.get('sacco')
            if not sacco and hasattr(self, 'user_sacco'):
                sacco = self.user_sacco
            
            if sacco:
                if self.instance.pk:
                    # Editing existing product
                    if LoanProduct.objects.filter(
                        product_code=product_code, 
                        sacco=sacco
                    ).exclude(pk=self.instance.pk).exists():
                        raise forms.ValidationError('A product with this code already exists')
                else:
                    # Creating new product
                    if LoanProduct.objects.filter(
                        product_code=product_code, 
                        sacco=sacco
                    ).exists():
                        raise forms.ValidationError('A product with this code already exists')
        return product_code

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            sacco = self.cleaned_data.get('sacco')
            if not sacco and hasattr(self, 'user_sacco'):
                sacco = self.user_sacco
            if sacco:
                if self.instance.pk:
                    if LoanProduct.objects.filter(name=name, sacco=sacco).exclude(pk=self.instance.pk).exists():
                        raise forms.ValidationError('A product with this name already exists')
                else:
                    if LoanProduct.objects.filter(name=name, sacco=sacco).exists():
                        raise forms.ValidationError('A product with this name already exists')
        return name


class RepaymentForm(forms.ModelForm):
    class Meta:
        model = LoanRepayment
        fields = ['amount', 'payment_method', 'reference_number', 'applied_to_principal', 'applied_to_interest']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter repayment amount', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter reference number (optional)'}),
            'applied_to_principal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Principal amount', 'step': '0.01'}),
            'applied_to_interest': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Interest amount', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        principal = cleaned_data.get('applied_to_principal') or 0
        interest = cleaned_data.get('applied_to_interest') or 0

        if amount and principal + interest > amount:
            raise forms.ValidationError('Principal + Interest cannot exceed total repayment amount.')

        # Auto-calculate if not provided
        if amount and not principal and not interest:
            # Default: 70% principal, 30% interest (can be customized)
            cleaned_data['applied_to_principal'] = amount * 0.7
            cleaned_data['applied_to_interest'] = amount * 0.3
        elif amount and not principal:
            cleaned_data['applied_to_principal'] = amount - interest
        elif amount and not interest:
            cleaned_data['applied_to_interest'] = amount - principal

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            # Check if loan is fully repaid after this repayment
            if instance.loan.is_fully_repaid:
                instance.loan.mark_as_closed()
                # Send notification about loan closure
                from notifications.services import NotificationService
                if instance.loan.member.user_account:
                    NotificationService.create_notification(
                        user=instance.loan.member.user_account,
                        title="Loan Fully Repaid",
                        message=f"Congratulations! Your loan {instance.loan.loan_number} has been fully repaid and closed.",
                        action_type='loan_approval',  # Using existing type
                        action_url=f"/loans/profile/{instance.loan.id}/",
                        priority='High',
                        sacco=instance.loan.member.sacco
                    )
        
        return instance
