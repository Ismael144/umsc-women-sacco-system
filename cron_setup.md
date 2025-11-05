# Loan Due Date Notification Setup

## Management Command

A Django management command has been created to check for loans approaching or past due dates and send notifications.

### Command Location
`loans/management/commands/check_loan_due_dates.py`

### Usage

```bash
# Check for loans due in 7 days (default)
python manage.py check_loan_due_dates

# Check for loans due in 14 days
python manage.py check_loan_due_dates --days-before 14

# Dry run to see what would be sent
python manage.py check_loan_due_dates --dry-run
```

### What it does

1. **Approaching Due Date**: Sends reminders to members and admins 7 days before loan maturity
2. **Overdue Loans**: Sends urgent notifications to members and admins for past due loans
3. **Notifications**: Creates in-app notifications with links to loan profiles
4. **Priority Levels**: 
   - High priority for approaching due dates
   - Critical priority for overdue loans

## Cron Job Setup

To run this automatically, add to your crontab:

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/your/project && python manage.py check_loan_due_dates

# Run twice daily (9 AM and 6 PM)
0 9,18 * * * cd /path/to/your/project && python manage.py check_loan_due_dates
```

## Notification Types

- **Payment Reminder**: For loans approaching due date
- **Loan Overdue**: For loans past due date

## Who Gets Notified

- **Members**: Get notifications about their own loans
- **Sacco Admins**: Get notifications about all loans in their sacco
- **Priority**: Overdue loans get Critical priority, reminders get High priority

## Testing

```bash
# Test with dry run
python manage.py check_loan_due_dates --dry-run

# Test with different days
python manage.py check_loan_due_dates --days-before 3
```






