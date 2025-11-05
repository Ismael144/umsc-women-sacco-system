"""
Constants for members app to ensure consistency across models, views, and templates
"""

# Member status choices - using the exact values from the model
MEMBER_STATUS_CHOICES = [
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
    ('Suspended', 'Suspended'),
    ('Prospect', 'Prospect'),
]

# Member status constants for programmatic use
MEMBER_STATUS_ACTIVE = 'Active'
MEMBER_STATUS_INACTIVE = 'Inactive'
MEMBER_STATUS_SUSPENDED = 'Suspended'
MEMBER_STATUS_PROSPECT = 'Prospect'

# Gender choices
GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

# Business registration status choices
BUSINESS_REGISTRATION_CHOICES = [
    ('Registered', 'Registered'),
    ('Informal', 'Informal'),
    ('None', 'None')
]

# Education level choices
EDUCATION_LEVEL_CHOICES = [
    ('None', 'None'),
    ('Primary', 'Primary'),
    ('Secondary', 'Secondary'),
    ('Tertiary', 'Tertiary'),
    ('University', 'University')
]

# Meeting frequency choices
MEETING_FREQUENCY_CHOICES = [
    ('Weekly', 'Weekly'),
    ('Monthly', 'Monthly'),
    ('Quarterly', 'Quarterly')
]

# Mobile wallet provider choices
MOBILE_WALLET_PROVIDER_CHOICES = [
    ('MTN', 'MTN Mobile Money'),
    ('Airtel', 'Airtel Money'),
    ('Equity', 'Equity Bank'),
    ('Other', 'Other')
]

# Document type choices
DOCUMENT_TYPE_CHOICES = [
    ('ID', 'National ID'),
    ('Passport', 'Passport'),
    ('Receipt', 'Receipt'),
    ('Contract', 'Contract'),
    ('Other', 'Other')
]

# Notification channel choices
NOTIFICATION_CHANNEL_CHOICES = [
    ('Email', 'Email'),
    ('SMS', 'SMS'),
    ('InApp', 'In-App'),
    ('Push', 'Push Notification')
]

# Notification priority choices
NOTIFICATION_PRIORITY_CHOICES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High'),
    ('Critical', 'Critical')
]










