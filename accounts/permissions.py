"""
Permission check functions for reusability across views
"""

def check_sacco_admin(user):
    """Check if user is a Sacco Admin or System Admin"""
    return user.is_authenticated and (user.is_sacco_admin or user.is_system_admin)


def check_regional_admin(user):
    """Check if user is a Regional Admin or System Admin"""
    return user.is_authenticated and (user.is_regional_admin or user.is_system_admin)


def check_system_admin(user):
    """Check if user is a System Admin"""
    return user.is_authenticated and user.is_system_admin


def check_admin(user):
    """Check if user is any type of admin"""
    return user.is_authenticated and (user.is_sacco_admin or user.is_regional_admin or user.is_system_admin)


def check_member_search_access(user):
    """Check if user can access member search (Sacco Admin, Regional Admin, or System Admin)"""
    return user.is_authenticated and (user.is_sacco_admin or user.is_regional_admin or user.is_system_admin)


def get_user_data_scope(user):
    """
    Get the data scope for a user based on their role
    Returns a dictionary with filter parameters for querysets
    """
    if not user.is_authenticated:
        return {'error': 'User not authenticated'}
    
    if user.is_system_admin:
        return {'scope': 'all', 'filters': {}}
    elif user.is_regional_admin:
        return {
            'scope': 'regional',
            'filters': {'sacco__region': user.region}
        }
    elif user.is_sacco_admin:
        return {
            'scope': 'sacco',
            'filters': {'sacco': user.sacco}
        }
    else:
        # Regular member - can only see their own data
        return {
            'scope': 'member',
            'filters': {'user_account': user}
        }


def filter_queryset_by_user_scope(queryset, user, model_type='member'):
    """
    Filter a queryset based on user's role and scope
    
    Args:
        queryset: The queryset to filter
        user: The current user
        model_type: Type of model ('member', 'loan', 'savings', etc.)
    
    Returns:
        Filtered queryset
    """
    if not user.is_authenticated:
        return queryset.none()
    
    if user.is_system_admin:
        return queryset
    
    elif user.is_regional_admin:
        if model_type == 'member':
            return queryset.filter(sacco__region=user.region)
        elif model_type == 'loan':
            return queryset.filter(member__sacco__region=user.region)
        elif model_type == 'savings':
            return queryset.filter(member__sacco__region=user.region)
        elif model_type == 'savings_transaction':
            return queryset.filter(account__member__sacco__region=user.region)
        elif model_type == 'saving_product':
            return queryset.filter(sacco__region=user.region)
        elif model_type == 'loan_product':
            return queryset.filter(sacco__region=user.region)
        elif model_type == 'loan_repayment':
            return queryset.filter(loan__member__sacco__region=user.region)
        elif model_type in ['funding', 'project', 'expense']:
            return queryset.filter(sacco__region=user.region)
        else:
            return queryset.filter(sacco__region=user.region)

    elif user.is_sacco_admin:
        if model_type == 'member':
            return queryset.filter(sacco=user.sacco)
        elif model_type == 'loan':
            return queryset.filter(member__sacco=user.sacco)
        elif model_type == 'savings':
            return queryset.filter(member__sacco=user.sacco)
        elif model_type == 'savings_transaction':
            return queryset.filter(account__member__sacco=user.sacco)
        elif model_type == 'saving_product':
            return queryset.filter(sacco=user.sacco)
        elif model_type == 'loan_product':
            return queryset.filter(sacco=user.sacco)
        elif model_type == 'loan_repayment':
            return queryset.filter(loan__member__sacco=user.sacco)
        elif model_type in ['funding', 'project', 'expense']:
            return queryset.filter(sacco=user.sacco)
        else:
            return queryset.filter(sacco=user.sacco)
    
    else:
        # Regular member - can only see their own data
        if model_type == 'member':
            return queryset.filter(user_account=user)
        elif model_type == 'loan':
            return queryset.filter(member__user_account=user)
        elif model_type == 'savings':
            return queryset.filter(member__user_account=user)
        elif model_type == 'savings_transaction':
            return queryset.filter(account__member__user_account=user)
        elif model_type == 'saving_product':
            # Members can see saving products from their sacco
            return queryset.filter(sacco=user.sacco)
        elif model_type == 'loan_product':
            # Members can see loan products from their sacco
            return queryset.filter(sacco=user.sacco)
        elif model_type == 'loan_repayment':
            # Members can see their own loan repayments
            return queryset.filter(loan__member__user_account=user)
        else:
            return queryset.none()


def can_access_member_data(user, member):
    """
    Check if user can access specific member data
    
    Args:
        user: The current user
        member: The member object to check access for
    
    Returns:
        Boolean indicating if access is allowed
    """
    if not user.is_authenticated:
        return False
    
    if user.is_system_admin:
        return True
    elif user.is_regional_admin:
        return member.sacco.region == user.region
    elif user.is_sacco_admin:
        return member.sacco == user.sacco
    else:
        # Regular member - can only access their own data
        return member.user_account == user


def get_accessible_saccos(user):
    """
    Get list of Saccos that user can access based on their role
    
    Args:
        user: The current user
    
    Returns:
        QuerySet of accessible Saccos
    """
    from .models import Sacco
    
    if not user.is_authenticated:
        return Sacco.objects.none()
    
    if user.is_system_admin:
        return Sacco.objects.all()
    elif user.is_regional_admin:
        return Sacco.objects.filter(region=user.region)
    elif user.is_sacco_admin:
        return Sacco.objects.filter(id=user.sacco.id)
    else:
        return Sacco.objects.none()


def get_accessible_members(user):
    """
    Get list of members that user can access based on their role
    
    Args:
        user: The current user
    
    Returns:
        QuerySet of accessible members
    """
    from members.models import Member
    
    if not user.is_authenticated:
        return Member.objects.none()
    
    if user.is_system_admin:
        return Member.objects.all()
    elif user.is_regional_admin:
        return Member.objects.filter(sacco__region=user.region)
    elif user.is_sacco_admin:
        return Member.objects.filter(sacco=user.sacco)
    else:
        # Regular member - can only see their own data
        return Member.objects.filter(user_account=user)
