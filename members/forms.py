from django import forms
from .models import Member, MemberGroup, MemberProfile


class MemberForm(forms.ModelForm):
    """Enhanced Member form with comprehensive fields"""
    
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
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter last name'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter other names (optional)'}),
            'gender': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True}),
            
            # Identification
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter national ID number'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter passport number'}),
            
            # Contact Information
            'phone': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            
            # Address Information
            'home_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'required': True, 'placeholder': 'Enter home address'}),
            'village_town': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter village or town'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter district'}),
            'subcounty': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subcounty'}),
            
            # Employment Information
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter occupation'}),
            'employer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter employer name'}),
            
            # Membership Information
                   'group': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            
            # Financial Information
            'shares_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'savings_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            
            # Additional Information
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter additional notes (optional)'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add required field indicators
        required_fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'phone', 'home_address', 'village_town', 'district']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
    
    def clean_national_id(self):
        national_id = self.cleaned_data.get('national_id')
        if national_id:
            # Check for uniqueness
            if self.instance.pk:
                # Editing existing member
                if Member.objects.filter(national_id=national_id).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('A member with this National ID already exists')
            else:
                # Creating new member
                if Member.objects.filter(national_id=national_id).exists():
                    raise forms.ValidationError('A member with this National ID already exists')
        return national_id
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Check for uniqueness
            if self.instance.pk:
                # Editing existing member
                if Member.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('A member with this phone number already exists')
            else:
                # Creating new member
                if Member.objects.filter(phone=phone).exists():
                    raise forms.ValidationError('A member with this phone number already exists')
        return phone


class MemberProfileForm(forms.ModelForm):
    """Enhanced Member Profile form with detailed information"""
    
    class Meta:
        model = MemberProfile
        fields = [
            'next_of_kin_name', 'next_of_kin_phone', 'relationship',
            'bank_name', 'bank_account_number', 'bank_branch',
            'kyc_complete', 'additional_documents'
        ]
        widgets = {
            'next_of_kin_name': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter next of kin full name'}),
            'next_of_kin_phone': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter next of kin phone number'}),
            'relationship': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter relationship (e.g., Spouse, Parent, Sibling)'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank name (optional)'}),
            'bank_account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank account number (optional)'}),
            'bank_branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank branch (optional)'}),
            'kyc_complete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'additional_documents': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class MemberGroupForm(forms.ModelForm):
    """Enhanced Member Group form"""
    
    class Meta:
        model = MemberGroup
        fields = ['name', 'code', 'description', 'leader', 'meeting_frequency', 'social_fund_balance', 'group_guarantee_limit']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter group name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter group code'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter group description'}),
                   'leader': forms.Select(attrs={'class': 'form-select'}),
            'meeting_frequency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Weekly, Monthly'}),
            'social_fund_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'group_guarantee_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }
    
    def __init__(self, *args, **kwargs):
        sacco = kwargs.pop('sacco', None)
        super().__init__(*args, **kwargs)
        # Populate leader choices with members in current sacco (all statuses per requirement b)
        if 'leader' in self.fields:
            qs = Member.objects.all()
            if sacco is not None:
                qs = qs.filter(sacco=sacco)
            self.fields['leader'].queryset = qs


class ComprehensiveMemberForm(forms.ModelForm):
    """Comprehensive member form combining Member and MemberProfile"""
    
    # MemberProfile fields
    next_of_kin_name = forms.CharField(max_length=100, required=True)
    next_of_kin_phone = forms.CharField(max_length=20, required=True)
    relationship = forms.CharField(max_length=50, required=True)
    bank_name = forms.CharField(max_length=100, required=False)
    bank_account_number = forms.CharField(max_length=20, required=False)
    bank_branch = forms.CharField(max_length=100, required=False)
    kyc_complete = forms.BooleanField(required=False)
    
    # Enhanced Member fields
    monthly_income = forms.DecimalField(max_digits=12, decimal_places=2, required=False)
    business_registration_status = forms.ChoiceField(choices=[
        ('Registered', 'Registered'),
        ('Informal', 'Informal'),
        ('None', 'None')
    ], required=False)
    autonomy_score = forms.IntegerField(min_value=0, max_value=10, required=False)
    
    # Enhanced MemberProfile fields
    business_type = forms.CharField(max_length=100, required=False)
    business_location = forms.CharField(max_length=200, required=False)
    years_in_business = forms.IntegerField(required=False)
    monthly_business_income = forms.DecimalField(max_digits=14, decimal_places=2, required=False)
    family_size = forms.IntegerField(required=False)
    education_level = forms.ChoiceField(choices=[
        ('None', 'None'),
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
        ('Tertiary', 'Tertiary'),
        ('University', 'University')
    ], required=False)
    
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
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter last name'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter other names (optional)'}),
            'gender': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True}),
            
            # Identification
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter national ID number'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter passport number'}),
            
            # Contact Information
            'phone': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            
            # Address Information
            'home_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'required': True, 'placeholder': 'Enter home address'}),
            'village_town': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter village or town'}),
            'district': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter district'}),
            'subcounty': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subcounty'}),
            
            # Employment Information
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter occupation'}),
            'employer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter employer name'}),
            
            # Membership Information
                   'group': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            
            # Financial Information
            'shares_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'savings_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            
            # Additional Information
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter additional notes (optional)'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add required field indicators
        required_fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'phone', 'home_address', 'village_town', 'district']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
        
        # Add profile fields widgets
        self.fields['next_of_kin_name'].widget = forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter next of kin full name'})
        self.fields['next_of_kin_phone'].widget = forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter next of kin phone number'})
        self.fields['relationship'].widget = forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Enter relationship (e.g., Spouse, Parent, Sibling)'})
        self.fields['bank_name'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank name (optional)'})
        self.fields['bank_account_number'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank account number (optional)'})
        self.fields['bank_branch'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bank branch (optional)'})
        self.fields['kyc_complete'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
        
        # Add enhanced fields widgets
        self.fields['monthly_income'].widget = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter monthly income'})
        self.fields['business_registration_status'].widget = forms.Select(attrs={'class': 'form-select'})
        self.fields['autonomy_score'].widget = forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10', 'placeholder': 'Enter autonomy score (0-10)'})
        self.fields['business_type'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter business type'})
        self.fields['business_location'].widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter business location'})
        self.fields['years_in_business'].widget = forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter years in business'})
        self.fields['monthly_business_income'].widget = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Enter monthly business income'})
        self.fields['family_size'].widget = forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter family size'})
        self.fields['education_level'].widget = forms.Select(attrs={'class': 'form-select'})
    
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
            
            # Save enhanced profile fields
            profile.business_type = self.cleaned_data.get('business_type', '')
            profile.business_location = self.cleaned_data.get('business_location', '')
            profile.years_in_business = self.cleaned_data.get('years_in_business')
            profile.monthly_business_income = self.cleaned_data.get('monthly_business_income')
            profile.family_size = self.cleaned_data.get('family_size', 1)
            profile.education_level = self.cleaned_data.get('education_level', 'Primary')
            
            profile.save()
        return member


class UmscWomenMemberRegistrationForm(forms.ModelForm):
    """Registration form that matches UMSC Women SACCO paper form."""
    # Section A - Personal Information
    full_name = forms.CharField(max_length=200, label='Full Name (as per National ID)')
    national_id = forms.CharField(max_length=20, label='National Identification Number (NIN)')
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Date of Birth')
    marital_status = forms.ChoiceField(choices=Member.MARITAL_STATUS_CHOICES, label='Marital Status')
    phone = forms.CharField(max_length=20, label='Contact Number')
    email = forms.EmailField(required=False, label='Email Address (if any)')
    home_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), label='Physical Address / Village')
    district = forms.CharField(max_length=50, label='District / Region')
    occupation = forms.CharField(max_length=100, required=False, label='Occupation / Source of Income')
    next_of_kin_name = forms.CharField(max_length=100, label='Next of Kin Name')
    relationship = forms.CharField(max_length=50, label='Relationship to Next of Kin')
    next_of_kin_phone = forms.CharField(max_length=20, label='Next of Kin Contact')

    # Section B - Membership Information
    membership_type = forms.ChoiceField(choices=Member.MEMBERSHIP_TYPE_CHOICES, label='Membership Type')
    membership_category = forms.ChoiceField(choices=Member.MEMBERSHIP_CATEGORY_CHOICES, label='Membership Category')
    date_joined = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Date of Joining')
    referred_by = forms.CharField(max_length=200, required=False, label='Referred By (if any)')
    initial_savings_deposit = forms.DecimalField(max_digits=14, decimal_places=2, label='Initial Savings Deposit (UGX)')
    monthly_contribution_commitment = forms.DecimalField(max_digits=14, decimal_places=2, label='Monthly Contribution Commitment (UGX)')
    preferred_payment_method = forms.ChoiceField(choices=Member.PAYMENT_METHOD_CHOICES, label='Preferred Payment Method')

    # Section D - Official Use Only
    # Note: application_received_by is set from request_user in save() method
    application_received_designation = forms.CharField(max_length=100, label='Designation / Office')
    application_received_at = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Date')
    approved_by_committee = forms.CharField(max_length=200, required=False, label='Approved By (SACCO Committee)')
    approval_remarks = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, label='Remarks')
    approval_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label='Approval Date')

    # Section E - Attachments
    attachment_id_copy = forms.FileField(required=False, label='Copy of National ID')
    attachment_passport_photo = forms.ImageField(required=False, label='Passport-size Photograph (1)')
    attachment_proof_initial_deposit = forms.FileField(required=False, label='Proof of Initial Savings Deposit')
    attachment_recommendation_letter = forms.FileField(required=False, label='Recommendation from Local Muslim Leader / Women Chairperson')

    # Section: Business & Empowerment Information (rendered in template)
    business_type = forms.CharField(max_length=100, required=False, label='Business Type')
    business_location = forms.CharField(max_length=200, required=False, label='Business Location')
    years_in_business = forms.IntegerField(required=False, label='Years in Business')
    monthly_business_income = forms.DecimalField(max_digits=14, decimal_places=2, required=False, label='Monthly Business Income')
    family_size = forms.IntegerField(required=False, label='Family Size')
    education_level = forms.ChoiceField(choices=[
        ('None', 'None'),
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
        ('Tertiary', 'Tertiary'),
        ('University', 'University')
    ], required=False, label='Education Level')

    # Employment Information (template section)
    employer_name = forms.CharField(max_length=200, required=False, label='Employer Name')
    monthly_income = forms.DecimalField(max_digits=12, decimal_places=2, required=False, label='Monthly Income')
    business_registration_status = forms.ChoiceField(choices=[
        ('Registered', 'Registered'),
        ('Informal', 'Informal'),
        ('None', 'None')
    ], required=False, label='Business Registration Status')
    autonomy_score = forms.IntegerField(min_value=0, max_value=10, required=False, label='Autonomy Score (0-10)')
    status = forms.ChoiceField(choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
        ('Prospect', 'Prospect'),
    ], required=False, label='Member Status')
    shares_balance = forms.DecimalField(max_digits=14, decimal_places=2, required=False, label='Initial Shares Balance')
    savings_balance = forms.DecimalField(max_digits=14, decimal_places=2, required=False, label='Initial Savings Balance')
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label='Additional Notes')

    class Meta:
        model = Member
        fields = []  # handled manually in save

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Map of field -> (css class, placeholder)
        text_controls = {
            'full_name': ('form-control', 'Enter full name as per National ID'),
            'national_id': ('form-control', 'Enter NIN'),
            'phone': ('form-control phone-mask', '+256 XXX XXX XXX or 0XXX XXX XXX'),
            'email': ('form-control', 'example@domain.com'),
            'district': ('form-control', 'Enter district or region'),
            'occupation': ('form-control', 'Enter occupation or income source'),
            'next_of_kin_name': ('form-control', 'Enter next of kin full name'),
            'relationship': ('form-control', 'e.g., Spouse, Parent'),
            'next_of_kin_phone': ('form-control phone-mask', '+256 XXX XXX XXX or 0XXX XXX XXX'),
            'referred_by': ('form-control', 'Enter referrer name (optional)'),
            'application_received_designation': ('form-control', 'e.g., Admin, Officer'),
            'approved_by_committee': ('form-control', 'Committee approver (optional)'),
            'employer_name': ('form-control', 'Enter employer name (optional)'),
        }

        textarea_controls = {
            'home_address': ('form-control', 'Enter physical address / village'),
            'approval_remarks': ('form-control', 'Enter remarks (optional)'),
            'notes': ('form-control', 'Enter additional notes (optional)'),
        }

        number_controls = {
            'initial_savings_deposit': ('form-control', '0.00'),
            'monthly_contribution_commitment': ('form-control', '0.00'),
            'years_in_business': ('form-control', ''),
            'monthly_business_income': ('form-control', '0.00'),
            'family_size': ('form-control', ''),
            'monthly_income': ('form-control', '0.00'),
            'autonomy_score': ('form-control', ''),
            'shares_balance': ('form-control', '0.00'),
            'savings_balance': ('form-control', '0.00'),
        }

        select_controls = {
            'marital_status': 'form-select',
            'membership_type': 'form-select',
            'membership_category': 'form-select',
            'preferred_payment_method': 'form-select',
            'education_level': 'form-select',
            'business_registration_status': 'form-select',
            'status': 'form-select',
        }

        date_controls = ['date_of_birth', 'date_joined', 'application_received_at', 'approval_date']

        # Apply widget classes/placeholders
        for name, (css, ph) in text_controls.items():
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': css, 'placeholder': ph})

        for name, (css, ph) in textarea_controls.items():
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': css, 'placeholder': ph, 'rows': 2})

        for name, (css, ph) in number_controls.items():
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': css, 'placeholder': ph, 'step': '0.01'})

        for name, css in select_controls.items():
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': css})

        for name in date_controls:
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'form-control'})

        # File inputs styling
        for name in ['attachment_id_copy', 'attachment_passport_photo', 'attachment_proof_initial_deposit', 'attachment_recommendation_letter']:
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'form-control'})
        # Required: Recommendation letter must be provided
        if 'attachment_recommendation_letter' in self.fields:
            self.fields['attachment_recommendation_letter'].required = True

        # Business & empowerment text inputs
        for name in ['business_type', 'business_location']:
            if name in self.fields:
                self.fields[name].widget.attrs.update({'class': 'form-control'})

        # Required fields per paper form
        required_fields = [
            'full_name', 'national_id', 'date_of_birth', 'marital_status', 'phone',
            'home_address', 'district', 'membership_type', 'membership_category',
            'date_joined', 'initial_savings_deposit', 'monthly_contribution_commitment',
            'preferred_payment_method', 'next_of_kin_name', 'relationship', 'next_of_kin_phone',
            'application_received_designation', 'application_received_at',
        ]
        for f in required_fields:
            if f in self.fields:
                self.fields[f].required = True

    def clean(self):
        cleaned = super().clean()
        # Enforce: at least one of passport photo OR ID copy must be provided
        id_copy = self.files.get('attachment_id_copy') or cleaned.get('attachment_id_copy')
        passport_photo = self.files.get('attachment_passport_photo') or cleaned.get('attachment_passport_photo')
        if not id_copy and not passport_photo:
            message = 'Provide either Passport-size Photograph or Copy of National ID.'
            self.add_error('attachment_id_copy', message)
            self.add_error('attachment_passport_photo', message)
        # Ensure recommendation letter is present (defensive)
        recommendation = self.files.get('attachment_recommendation_letter') or cleaned.get('attachment_recommendation_letter')
        if not recommendation:
            self.add_error('attachment_recommendation_letter', 'This attachment is required.')
        return cleaned

    def clean_full_name(self):
        name = self.cleaned_data['full_name'].strip()
        parts = [p for p in name.split() if p]
        if len(parts) < 2:
            raise forms.ValidationError('Please provide at least first and last name.')
        return name

    def save(self, request_user, commit=True, sacco=None):
        # Split full name
        full_name = self.cleaned_data['full_name']
        parts = [p for p in full_name.split() if p]
        first_name = parts[0]
        last_name = parts[-1]
        other_names = ' '.join(parts[1:-1]) if len(parts) > 2 else ''

        # Use provided sacco or fall back to request_user's sacco
        member_sacco = sacco if sacco else request_user.sacco

        member = Member(
            sacco=member_sacco,
            first_name=first_name,
            last_name=last_name,
            other_names=other_names or None,
            gender='Female',  # Women SACCO default; can be adjusted if needed
            national_id=self.cleaned_data['national_id'],
            date_of_birth=self.cleaned_data['date_of_birth'],
            marital_status=self.cleaned_data['marital_status'],
            phone=self.cleaned_data['phone'],
            email=self.cleaned_data.get('email'),
            home_address=self.cleaned_data['home_address'],
            village_town=self.cleaned_data['home_address'],  # map to same if not separately provided
            district=self.cleaned_data['district'],
            occupation=self.cleaned_data.get('occupation'),
            membership_type=self.cleaned_data['membership_type'],
            membership_category=self.cleaned_data['membership_category'],
            referred_by=self.cleaned_data.get('referred_by'),
            preferred_payment_method=self.cleaned_data['preferred_payment_method'],
            monthly_contribution_commitment=self.cleaned_data['monthly_contribution_commitment'],
            date_joined=self.cleaned_data['date_joined'],
            created_by=request_user,
            application_received_by=request_user,
            application_received_designation=self.cleaned_data['application_received_designation'],
            application_received_at=self.cleaned_data['application_received_at'],
            approved_by_committee=self.cleaned_data.get('approved_by_committee'),
            approval_remarks=self.cleaned_data.get('approval_remarks'),
            approval_date=self.cleaned_data.get('approval_date'),
        )

        # Attachments
        for field in [
            'attachment_id_copy',
            'attachment_passport_photo',
            'attachment_proof_initial_deposit',
            'attachment_recommendation_letter',
        ]:
            file = self.files.get(field)
            if file:
                setattr(member, field, file)

        if commit:
            member.save()

            # Create/update MemberProfile with Next of Kin
            profile, _ = MemberProfile.objects.get_or_create(member=member)
            profile.next_of_kin_name = self.cleaned_data['next_of_kin_name']
            profile.next_of_kin_phone = self.cleaned_data['next_of_kin_phone']
            profile.relationship = self.cleaned_data['relationship']
            # Business & empowerment fields
            profile.business_type = self.cleaned_data.get('business_type') or ''
            profile.business_location = self.cleaned_data.get('business_location') or ''
            profile.years_in_business = self.cleaned_data.get('years_in_business')
            profile.monthly_business_income = self.cleaned_data.get('monthly_business_income')
            profile.family_size = self.cleaned_data.get('family_size') or 1
            profile.education_level = self.cleaned_data.get('education_level') or 'Primary'
            profile.save()

        # Map additional employment/member fields
        member.employer_name = self.cleaned_data.get('employer_name') or ''
        member.monthly_income = self.cleaned_data.get('monthly_income')
        member.business_registration_status = self.cleaned_data.get('business_registration_status') or member.business_registration_status
        member.autonomy_score = self.cleaned_data.get('autonomy_score') or member.autonomy_score
        member.status = self.cleaned_data.get('status') or member.status
        member.shares_balance = self.cleaned_data.get('shares_balance') or member.shares_balance
        # Align model savings_balance with initial deposit for consistency if provided
        member.savings_balance = self.cleaned_data.get('initial_savings_deposit') or member.savings_balance
        member.notes = self.cleaned_data.get('notes') or member.notes
        member.save()

        # Return member and finance data for caller to handle account/transaction
        return member, self.cleaned_data['initial_savings_deposit']
