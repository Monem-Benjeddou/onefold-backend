from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class RevenueModel(AbstractAutoIncrementModel):
    """
    Revenue model types that can be assigned to startups.
    These are configurable by admin and can be changed.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Name of the revenue model")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Description of how this revenue model works")
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Order for displaying models (lower numbers first)")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this revenue model is currently available for selection")
    )
    
    class Meta:
        verbose_name = _("Revenue Model")
        verbose_name_plural = _("Revenue Models")
        db_table = "revenue_model"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class StartupRevenueModel(AbstractAutoIncrementModel):
    """
    Links startups to their revenue models (many-to-many relationship).
    """
    
    startup = models.ForeignKey(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='revenue_models',
        help_text=_("The startup this revenue model belongs to")
    )
    
    revenue_model = models.ForeignKey(
        RevenueModel,
        on_delete=models.CASCADE,
        help_text=_("The revenue model used by the startup")
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text=_("Whether this is the primary revenue model")
    )
    
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Percentage of revenue from this model")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Additional details about how this model is implemented")
    )
    
    class Meta:
        verbose_name = _("Startup Revenue Model")
        verbose_name_plural = _("Startup Revenue Models")
        db_table = "startup_revenue_model"
        unique_together = ['startup', 'revenue_model']
        ordering = ['-is_primary', 'revenue_model__order']
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['revenue_model']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.startup.startup_name} - {self.revenue_model.name}"
