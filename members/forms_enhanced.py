"""
Enhanced Forms with Comprehensive Placeholders
"""

from django import forms
from .models import Member, MemberGroup, MemberProfile


class MemberForm(forms.ModelForm):
    """Enhanced Member form with comprehensive fields and placeholders"""
    
    class Meta:
        model = Member
        fields = [
            # Basic Information
            'first_name', 'last_name', 'other_names', 'gender', 'date_of_birth',
            
            # Identification
            'national_id', 'passport_number',
            
            # Contact Information
            'phone', 'email',
            
            # Address Information
            'home_address', 'village_town', 'district', 'subcounty',
            
            # Employment Information
            'occupation', 'employer_name',
            
            # Membership Information
            'group', 'status',
            
            # Financial Information
            'shares_balance', 'savings_balance',
            
            # Additional Information
            'notes', 'photo'
        ]
        widgets = {
            # Basic Information
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter last name'
            }),
            'other_names': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter other names (optional)'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select', 
                'required': True
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control', 
                'required': True
            }),
            
            # Identification
            'national_id': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter National ID number'
            }),
            'passport_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter passport number (optional)'
            }),
            
            # Contact Information
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter email address (optional)'
            }),
            
            # Address Information
            'home_address': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter complete home address'
            }),
            'village_town': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter village or town name'
            }),
            'district': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter district name'
            }),
            'subcounty': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter sub-county name (optional)'
            }),
            
            # Employment Information
            'occupation': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter occupation (optional)'
            }),
            'employer_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter employer name (optional)'
            }),
            
            # Membership Information
            'group': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            
            # Financial Information
            'shares_balance': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
            'savings_balance': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
            
            # Additional Information
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control', 
                'placeholder': 'Enter any additional notes or comments'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control', 
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add required field indicators
        required_fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'phone', 'home_address', 'village_town', 'district']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True


class MemberProfileForm(forms.ModelForm):
    """Enhanced Member Profile form with detailed information and placeholders"""
    
    class Meta:
        model = MemberProfile
        fields = [
            'next_of_kin_name', 'next_of_kin_phone', 'relationship',
            'bank_name', 'bank_account_number', 'bank_branch',
            'kyc_complete', 'additional_documents'
        ]
        widgets = {
            'next_of_kin_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter next of kin full name'
            }),
            'next_of_kin_phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter next of kin phone number'
            }),
            'relationship': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter relationship (e.g., Spouse, Parent, Sibling)'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter bank name (optional)'
            }),
            'bank_account_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter bank account number (optional)'
            }),
            'bank_branch': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter bank branch (optional)'
            }),
            'kyc_complete': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'additional_documents': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control', 
                'placeholder': 'Enter any additional document information'
            }),
        }


class MemberGroupForm(forms.ModelForm):
    """Enhanced Member Group form with placeholders"""
    
    class Meta:
        model = MemberGroup
        fields = ['name', 'code', 'description', 'leader']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter group name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter group code (e.g., GRP001)'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control', 
                'placeholder': 'Enter group description'
            }),
            'leader': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate leader choices with active members
        if 'leader' in self.fields:
            from .constants import MEMBER_STATUS_ACTIVE
            self.fields['leader'].queryset = Member.objects.filter(status=MEMBER_STATUS_ACTIVE)


class ComprehensiveMemberForm(forms.ModelForm):
    """Comprehensive member form combining Member and MemberProfile with placeholders"""
    
    # MemberProfile fields
    next_of_kin_name = forms.CharField(max_length=100, required=True)
    next_of_kin_phone = forms.CharField(max_length=20, required=True)
    relationship = forms.CharField(max_length=50, required=True)
    bank_name = forms.CharField(max_length=100, required=False)
    bank_account_number = forms.CharField(max_length=20, required=False)
    bank_branch = forms.CharField(max_length=100, required=False)
    kyc_complete = forms.BooleanField(required=False)
    
    class Meta:
        model = Member
        fields = [
            # Basic Information
            'first_name', 'last_name', 'other_names', 'gender', 'date_of_birth',
            
            # Identification
            'national_id', 'passport_number',
            
            # Contact Information
            'phone', 'email',
            
            # Address Information
            'home_address', 'village_town', 'district', 'subcounty',
            
            # Employment Information
            'occupation', 'employer_name',
            
            # Membership Information
            'group', 'status',
            
            # Financial Information
            'shares_balance', 'savings_balance',
            
            # Additional Information
            'notes', 'photo'
        ]
        widgets = {
            # Basic Information
            'first_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter last name'
            }),
            'other_names': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter other names (optional)'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select', 
                'required': True
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control', 
                'required': True
            }),
            
            # Identification
            'national_id': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter National ID number'
            }),
            'passport_number': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter passport number (optional)'
            }),
            
            # Contact Information
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter phone number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter email address (optional)'
            }),
            
            # Address Information
            'home_address': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter complete home address'
            }),
            'village_town': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter village or town name'
            }),
            'district': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': True, 
                'placeholder': 'Enter district name'
            }),
            'subcounty': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter sub-county name (optional)'
            }),
            
            # Employment Information
            'occupation': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter occupation (optional)'
            }),
            'employer_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter employer name (optional)'
            }),
            
            # Membership Information
            'group': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            
            # Financial Information
            'shares_balance': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
            'savings_balance': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0.00'
            }),
            
            # Additional Information
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control', 
                'placeholder': 'Enter any additional notes or comments'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control', 
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add required field indicators
        required_fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'phone', 'home_address', 'village_town', 'district']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # Add profile fields widgets with placeholders
        self.fields['next_of_kin_name'].widget = forms.TextInput(attrs={
            'class': 'form-control', 
            'required': True, 
            'placeholder': 'Enter next of kin full name'
        })
        self.fields['next_of_kin_phone'].widget = forms.TextInput(attrs={
            'class': 'form-control', 
            'required': True, 
            'placeholder': 'Enter next of kin phone number'
        })
        self.fields['relationship'].widget = forms.TextInput(attrs={
            'class': 'form-control', 
            'required': True, 
            'placeholder': 'Enter relationship (e.g., Spouse, Parent, Sibling)'
        })
        self.fields['bank_name'].widget = forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter bank name (optional)'
        })
        self.fields['bank_account_number'].widget = forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter bank account number (optional)'
        })
        self.fields['bank_branch'].widget = forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter bank branch (optional)'
        })
        self.fields['kyc_complete'].widget = forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    
    def save(self, commit=True):
        member = super().save(commit=commit)
        if commit:
            # Create or update MemberProfile
            profile, created = MemberProfile.objects.get_or_create(member=member)
            profile.next_of_kin_name = self.cleaned_data['next_of_kin_name']
            profile.next_of_kin_phone = self.cleaned_data['next_of_kin_phone']
            profile.relationship = self.cleaned_data['relationship']
            profile.bank_name = self.cleaned_data['bank_name']
            profile.bank_account_number = self.cleaned_data['bank_account_number']
            profile.bank_branch = self.cleaned_data['bank_branch']
            profile.kyc_complete = self.cleaned_data['kyc_complete']
            profile.save()
        return member

