"""
Constants for loans app to ensure consistency across models, views, and templates
"""

# Loan status choices - using the exact values from the model
LOAN_STATUS_CHOICES = [
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

# Loan status constants for programmatic use
LOAN_STATUS_PENDING_APPROVAL = 'pending_approval'
LOAN_STATUS_APPROVED = 'approved'
LOAN_STATUS_PENDING_DISBURSEMENT = 'pending_disbursement'
LOAN_STATUS_DISBURSED = 'disbursed'
LOAN_STATUS_ACTIVE = 'active'
LOAN_STATUS_CLOSED = 'closed'
LOAN_STATUS_DECLINED = 'declined'
LOAN_STATUS_WITHDRAWN = 'withdrawn'
LOAN_STATUS_WRITTEN_OFF = 'written_off'
LOAN_STATUS_DEFAULTED = 'defaulted'

# Interest type choices
INTEREST_TYPE_CHOICES = [
    ('Flat', 'Flat Rate'),
    ('Reducing', 'Reducing Balance'),
]

# Collateral type choices
COLLATERAL_TYPE_CHOICES = [
    ('GroupGuarantee', 'Group Guarantee'),
    ('MovableAsset', 'Movable Asset'),
    ('TitleDeed', 'Title Deed'),
    ('Vehicle', 'Vehicle'),
    ('Other', 'Other')
]

# Charge type choices
CHARGE_TYPE_CHOICES = [
    ('ProcessingFee', 'Processing Fee'),
    ('LatePenalty', 'Late Payment Penalty'),
    ('Insurance', 'Insurance'),
    ('Other', 'Other')
]

# Payment method choices
PAYMENT_METHOD_CHOICES = [
    ('Cash', 'Cash'),
    ('Bank Transfer', 'Bank Transfer'),
    ('Mobile Money', 'Mobile Money'),
    ('Cheque', 'Cheque'),
    ('Other', 'Other')
]

# Status mapping for dashboard compatibility
DASHBOARD_STATUS_MAPPING = {
    'pending': 'pending_approval',
    'approved': 'approved',
    'rejected': 'declined',
    'active': 'active',
}










