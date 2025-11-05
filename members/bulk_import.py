"""
Bulk import functionality for members
"""

import csv
import io
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.utils import timezone
from .models import Member, MemberProfile
from .constants import MEMBER_STATUS_ACTIVE

User = get_user_model()


class MemberBulkImportForm(forms.Form):
    """Form for bulk importing members from CSV/Excel"""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text="Upload a CSV or Excel file with member data"
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            if not file.name.lower().endswith(('.csv', '.xlsx', '.xls')):
                raise forms.ValidationError('File must be a CSV or Excel file')
            
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 5MB')
        
        return file


class MemberBulkImporter:
    """Handles bulk import of members from CSV/Excel files"""
    
    REQUIRED_FIELDS = [
        'first_name', 'last_name', 'phone', 'gender', 'date_of_birth',
        'home_address', 'village_town', 'district'
    ]
    
    OPTIONAL_FIELDS = [
        'other_names', 'national_id', 'passport_number', 'email',
        'subcounty', 'occupation', 'employer_name', 'monthly_income',
        'next_of_kin_name', 'next_of_kin_phone', 'relationship',
        'bank_name', 'bank_account_number', 'bank_branch'
    ]
    
    def __init__(self, sacco, created_by):
        self.sacco = sacco
        self.created_by = created_by
        self.errors = []
        self.success_count = 0
        self.skipped_count = 0
    
    def import_from_csv(self, file):
        """Import members from CSV file"""
        try:
            # Read CSV content
            content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content))
            
            # Validate headers
            headers = csv_reader.fieldnames
            missing_fields = [field for field in self.REQUIRED_FIELDS if field not in headers]
            if missing_fields:
                self.errors.append(f"Missing required columns: {', '.join(missing_fields)}")
                return False
            
            # Process each row
            for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (header is row 1)
                try:
                    self._process_member_row(row, row_num)
                except Exception as e:
                    self.errors.append(f"Row {row_num}: {str(e)}")
                    self.skipped_count += 1
            
            return len(self.errors) == 0
            
        except Exception as e:
            self.errors.append(f"Error reading file: {str(e)}")
            return False
    
    def _process_member_row(self, row, row_num):
        """Process a single member row"""
        # Validate required fields
        for field in self.REQUIRED_FIELDS:
            if not row.get(field, '').strip():
                raise ValueError(f"Missing required field: {field}")
        
        # Check for duplicate phone number
        phone = row['phone'].strip()
        if Member.objects.filter(phone=phone).exists():
            raise ValueError(f"Phone number {phone} already exists")
        
        # Check for duplicate national ID if provided
        national_id = row.get('national_id', '').strip()
        if national_id and Member.objects.filter(national_id=national_id).exists():
            raise ValueError(f"National ID {national_id} already exists")
        
        # Generate member number
        member_count = Member.objects.filter(sacco=self.sacco).count() + 1
        member_number = f"MEM{member_count:04d}"
        
        # Generate username
        first_name = row['first_name'].strip()
        last_name = row['last_name'].strip()
        email = row.get('email', '').strip()
        
        if email:
            username = email.split('@')[0]
        else:
            username = f"{first_name.lower()}{last_name.lower()}"
        
        # Make username unique
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        # Generate temporary password
        temp_password = get_random_string(12)
        
        # Create User account
        user = User.objects.create_user(
            username=username,
            email=email or f"{username}@sacco.com",
            password=temp_password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            sacco=self.sacco,
            is_active=True
        )
        
        # Create Member record
        member = Member.objects.create(
            sacco=self.sacco,
            user_account=user,
            member_number=member_number,
            first_name=first_name,
            last_name=last_name,
            other_names=row.get('other_names', '').strip() or None,
            email=email or None,
            phone=phone,
            national_id=national_id or None,
            passport_number=row.get('passport_number', '').strip() or None,
            gender=row['gender'].strip(),
            date_of_birth=self._parse_date(row['date_of_birth']),
            home_address=row['home_address'].strip(),
            village_town=row['village_town'].strip(),
            district=row['district'].strip(),
            subcounty=row.get('subcounty', '').strip() or None,
            occupation=row.get('occupation', '').strip() or None,
            employer_name=row.get('employer_name', '').strip() or None,
            monthly_income=self._parse_decimal(row.get('monthly_income', '0')),
            status=MEMBER_STATUS_ACTIVE,
            date_joined=timezone.now().date(),
            created_by=self.created_by
        )
        
        # Create MemberProfile if profile data is provided
        if any(row.get(field, '').strip() for field in ['next_of_kin_name', 'next_of_kin_phone', 'relationship']):
            profile = MemberProfile.objects.create(
                member=member,
                next_of_kin_name=row.get('next_of_kin_name', '').strip() or None,
                next_of_kin_phone=row.get('next_of_kin_phone', '').strip() or None,
                relationship=row.get('relationship', '').strip() or None,
                bank_name=row.get('bank_name', '').strip() or None,
                bank_account_number=row.get('bank_account_number', '').strip() or None,
                bank_branch=row.get('bank_branch', '').strip() or None,
            )
        
        self.success_count += 1
    
    def _parse_date(self, date_str):
        """Parse date string in various formats"""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return timezone.datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"Invalid date format: {date_str}")
    
    def _parse_decimal(self, value):
        """Parse decimal value"""
        if not value or value.strip() == '':
            return 0
        
        try:
            return float(value.strip().replace(',', ''))
        except ValueError:
            return 0
    
    def get_summary(self):
        """Get import summary"""
        return {
            'success_count': self.success_count,
            'skipped_count': self.skipped_count,
            'error_count': len(self.errors),
            'errors': self.errors
        }










