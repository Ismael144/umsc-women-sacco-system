from django.db import models
from django.utils import timezone
from accounts.models import Sacco


class SaccoReviewPeriod(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, related_name='review_periods')
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sacco', 'name')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.sacco.name} - {self.name}"


class SaccoKRA(models.Model):
    sacco = models.ForeignKey(Sacco, on_delete=models.CASCADE, related_name='kras')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text='Weight 0-100')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class SaccoKPI(models.Model):
    DIRECTION_CHOICES = [
        ('higher_is_better', 'Higher is better'),
        ('lower_is_better', 'Lower is better'),
    ]

    UNIT_CHOICES = [
        ('count', 'Count'),
        ('percent', 'Percent'),
        ('ugx', 'UGX'),
    ]

    kra = models.ForeignKey(SaccoKRA, on_delete=models.CASCADE, related_name='kpis')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='count')
    target_value = models.DecimalField(max_digits=16, decimal_places=2)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text='Weight 0-100')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='higher_is_better')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SaccoKPIResult(models.Model):
    kpi = models.ForeignKey(SaccoKPI, on_delete=models.CASCADE, related_name='results')
    period = models.ForeignKey(SaccoReviewPeriod, on_delete=models.CASCADE, related_name='results')
    actual_value = models.DecimalField(max_digits=16, decimal_places=2)
    notes = models.TextField(blank=True)
    entered_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    entered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('kpi', 'period')

    def __str__(self):
        return f"{self.kpi.name} - {self.period.name}"

    @property
    def achievement_percent(self) -> float:
        try:
            if self.kpi.direction == 'higher_is_better':
                return float((self.actual_value / self.kpi.target_value) * 100)
            # lower is better
            ratio = float(self.kpi.target_value / self.actual_value) if self.actual_value else 0.0
            return max(0.0, min(200.0, ratio * 100))
        except Exception:
            return 0.0

    @property
    def weighted_score(self) -> float:
        # KPI score = achievement% * (kpi.weight/100)
        return self.achievement_percent * float(self.kpi.weight) / 100.0

# Create your models here.
