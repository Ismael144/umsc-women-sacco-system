# Sacco Management System

A comprehensive Django-based Sacco (Savings and Credit Cooperative) management system with a modern, responsive UI.

## Features

### Dashboard
- Total member count
- Loans disbursed
- Total savings
- Funding received
- Loan repayments over time (Chart)
- Membership by gender (Pie chart)
- Expected loan repayments for this month
- Last added savings

### Member Management
- Register Member
- Member Profiles
- Member Groups
- Inactive Members

### Savings Management
- Add Savings
- Savings Accounts
- Statements
- Saving Products

### Loan Management
- Add Loan
- View All Loans
- Loan Statistics
- All Borrowers
- Pending Approval
- Pending Disbursement
- Loans Declined
- Loans Withdrawn
- Loans Written off
- Loans closed
- Loans Approved
- Disbursed Loans
- Repayments
- Loan Profile
- Manage Loan Products

### Funding Management
- Add/Track funding
- Funds Allocation
- Expenditure Logs
- Funding Sources

### Project Management
- Add Project
- Existing Projects

### Expense Management
- Expenses
- Settings

### Reporting
- Loan Report
- Member Report
- Funding Report

### Administration
- User management
- Documents update

## Technology Stack

- **Backend**: Django 4.2.7
- **Frontend**: Bootstrap 5.3.0
- **Charts**: Chart.js
- **Data Tables**: DataTables
- **Icons**: Boxicons
- **Alerts**: SweetAlert2

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Create sample data:
```bash
python manage.py create_sample_data
```

4. Run the development server:
```bash
python manage.py runserver
```

## Default Login Credentials

- **System Admin**: admin/admin123
- **Sacco Admin**: sacco_admin/admin123

## Features Implemented

✅ Complete Django project structure
✅ Custom User model with Sacco association
✅ All required models (Members, Savings, Loans, Funding, Projects, Expenses)
✅ Authentication system with role-based access
✅ Responsive sidebar navigation
✅ Dashboard with statistics and charts
✅ Member management system
✅ Savings management
✅ Loan management system
✅ Funding tracking
✅ Project management
✅ Expense management
✅ Reporting system
✅ Modern UI with Bootstrap and custom styling
✅ DataTables integration
✅ SweetAlert2 for user interactions
✅ Chart.js for analytics

## Usage

1. Access the system at `http://localhost:8000`
2. Login with the provided credentials
3. Navigate through the sidebar to access different features
4. All pages are functional with proper data display and forms

## Customization

The system is designed to be easily customizable:
- Modify models in respective app files
- Update templates in the `templates/` directory
- Customize styling in the base template
- Add new features by creating new views and templates

## Support

For any issues or questions, please refer to the Django documentation or create an issue in the project repository.
