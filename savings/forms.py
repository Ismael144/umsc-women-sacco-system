from django import forms
from .models import SavingsTransaction, SavingProduct, SavingsAccount


class AddSavingsForm(forms.ModelForm):
    class Meta:
        model = SavingsTransaction
        fields = ['account', 'txn_type', 'amount', 'running_balance', 'reference', 'narration', 'mobile_money_tx_id']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'txn_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount to deposit', 'step': '0.01'}),
            'running_balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter running balance', 'step': '0.01'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter reference number'}),
            'narration': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter transaction description'}),
            'mobile_money_tx_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile money transaction ID'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        txn_type = cleaned_data.get('txn_type')
        amount = cleaned_data.get('amount')

        if not account:
            self.add_error('account', 'Please select a savings account.')
            return cleaned_data

        if amount is None or amount <= 0:
            self.add_error('amount', 'Amount must be greater than zero.')
            return cleaned_data

        # Determine previous balance (prefer account.balance; fallback to last transaction)
        previous_balance = account.balance
        if previous_balance is None:
            last_txn = account.transactions.order_by('-performed_at', '-id').first()
            previous_balance = last_txn.running_balance if last_txn else 0

        # Compute the expected running balance based on transaction type
        additions = {'Deposit', 'Interest', 'Transfer'}
        subtractions = {'Withdrawal', 'Fee'}

        if txn_type in additions:
            expected_balance = previous_balance + amount
        elif txn_type in subtractions:
            # Prevent overdraft
            if amount > previous_balance:
                self.add_error('amount', 'Insufficient balance for this transaction.')
                return cleaned_data
            expected_balance = previous_balance - amount
        else:
            # Unknown type (should not happen due to choices)
            self.add_error('txn_type', 'Invalid transaction type.')
            return cleaned_data

        # Force the running balance to the computed value
        cleaned_data['running_balance'] = expected_balance
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Ensure running_balance matches computed value and update account balance
        account = instance.account
        additions = {'Deposit', 'Interest', 'Transfer'}
        if instance.txn_type in additions:
            instance.running_balance = (account.balance or 0) + instance.amount
        else:
            instance.running_balance = (account.balance or 0) - instance.amount

        if commit:
            instance.save()
            # Update the account's current balance to reflect the new running balance
            account.balance = instance.running_balance
            account.save(update_fields=['balance'])
        return instance


class SavingsAccountForm(forms.ModelForm):
    class Meta:
        model = SavingsAccount
        fields = ['member', 'product', 'account_number', 'balance']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter account number'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
        }


class SavingProductForm(forms.ModelForm):
    class Meta:
        model = SavingProduct
        fields = ['name', 'product_code', 'description', 'minimum_balance', 'max_balance', 'interest_rate', 'is_term_product', 'term_months', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name', 'required': True}),
            'product_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product code', 'required': True}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter product description', 'required': True}),
            'minimum_balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'required': True, 'min': '0'}),
            'max_balance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'required': True, 'min': '0', 'max': '100'}),
            'term_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter term in months', 'min': '1'}),
            'is_term_product': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        minimum_balance = cleaned_data.get('minimum_balance')
        max_balance = cleaned_data.get('max_balance')
        is_term_product = cleaned_data.get('is_term_product')
        term_months = cleaned_data.get('term_months')
        
        # Validate maximum balance is greater than minimum balance
        if minimum_balance and max_balance and max_balance <= minimum_balance:
            raise forms.ValidationError('Maximum balance must be greater than minimum balance.')
        
        # Validate term months for term products
        if is_term_product and not term_months:
            raise forms.ValidationError('Term months is required for term products.')
        
        if not is_term_product and term_months:
            cleaned_data['term_months'] = None
        
        return cleaned_data
