from django import forms
from .models import SaccoReviewPeriod, SaccoKRA, SaccoKPI, SaccoKPIResult


class ReviewPeriodForm(forms.ModelForm):
    class Meta:
        model = SaccoReviewPeriod
        fields = ['name', 'start_date', 'end_date', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class KRAForm(forms.ModelForm):
    class Meta:
        model = SaccoKRA
        fields = ['title', 'description', 'weight', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class KPIForm(forms.ModelForm):
    class Meta:
        model = SaccoKPI
        fields = ['name', 'description', 'unit', 'target_value', 'weight', 'direction', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'target_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class KPIResultForm(forms.ModelForm):
    class Meta:
        model = SaccoKPIResult
        fields = ['actual_value', 'notes']
        widgets = {
            'actual_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }









