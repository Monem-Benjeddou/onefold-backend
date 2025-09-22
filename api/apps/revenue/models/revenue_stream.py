from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class RevenueStream(AbstractAutoIncrementModel):
    """
    Revenue streams for startups with detailed financial information.
    """
    
    startup = models.ForeignKey(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='revenue_streams',
        help_text=_("The startup this revenue stream belongs to")
    )
    
    name = models.CharField(
        max_length=255,
        help_text=_("Name of the revenue stream")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Description of the revenue stream")
    )
    
    monthly_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Monthly revenue from this stream")
    )
    
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Annual revenue from this stream")
    )
    
    revenue_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Percentage of total revenue from this stream")
    )
    
    is_recurring = models.BooleanField(
        default=False,
        help_text=_("Whether this is a recurring revenue stream")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this revenue stream is currently active")
    )
    
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("When this revenue stream started")
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("When this revenue stream ended (if applicable)")
    )
    
    class Meta:
        verbose_name = _("Revenue Stream")
        verbose_name_plural = _("Revenue Streams")
        db_table = "revenue_stream"
        ordering = ['-revenue_percentage', 'name']
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['is_recurring']),
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date']),
        ]
    
    def __str__(self):
        return f"{self.startup.startup_name} - {self.name}"
    
    @property
    def monthly_revenue_formatted(self):
        """Return formatted monthly revenue."""
        if self.monthly_revenue:
            if self.monthly_revenue >= 1_000_000:
                return f"${self.monthly_revenue / 1_000_000:.2f}M"
            elif self.monthly_revenue >= 1_000:
                return f"${self.monthly_revenue / 1_000:.2f}K"
            else:
                return f"${self.monthly_revenue:.2f}"
        return None
    
    @property
    def annual_revenue_formatted(self):
        """Return formatted annual revenue."""
        if self.annual_revenue:
            if self.annual_revenue >= 1_000_000_000:
                return f"${self.annual_revenue / 1_000_000_000:.2f}B"
            elif self.annual_revenue >= 1_000_000:
                return f"${self.annual_revenue / 1_000_000:.2f}M"
            elif self.annual_revenue >= 1_000:
                return f"${self.annual_revenue / 1_000:.2f}K"
            else:
                return f"${self.annual_revenue:.2f}"
        return None

