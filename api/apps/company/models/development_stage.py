from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class DevelopmentStage(AbstractAutoIncrementModel):
    """
    Development stages that can be assigned to startups.
    These are configurable by admin and can be changed.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("Name of the development stage")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Description of what this stage represents")
    )
    
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Order for displaying stages (lower numbers first)")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this stage is currently available for selection")
    )
    
    
    class Meta:
        app_label = "company"
        verbose_name = _("Development Stage")
        verbose_name_plural = _("Development Stages")
        db_table = "development_stage"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name


class StartupDevelopmentStage(AbstractAutoIncrementModel):
    """
    Links startups to their current development stage.
    """
    
    startup = models.OneToOneField(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='development_stage',
        help_text=_("The startup this stage belongs to")
    )
    
    stage = models.ForeignKey(
        DevelopmentStage,
        on_delete=models.CASCADE,
        help_text=_("Current development stage of the startup")
    )
    
    assigned_date = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When this stage was assigned")
    )
    
    notes = models.TextField(
        blank=True,
        help_text=_("Additional notes about the stage assignment")
    )
    
    class Meta:
        app_label = "company"
        verbose_name = _("Startup Development Stage")
        verbose_name_plural = _("Startup Development Stages")
        db_table = "startup_development_stage"
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['stage']),
            models.Index(fields=['assigned_date']),
        ]
    
    def __str__(self):
        return f"{self.startup.startup_name} - {self.stage.name}"
