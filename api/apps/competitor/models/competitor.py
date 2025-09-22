from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class Competitor(AbstractAutoIncrementModel):
    """
    Competitors of startups categorized by market scope.
    """
    
    COMPETITOR_TYPE_CHOICES = [
        ('local', _('Local')),
        ('gcc', _('GCC (Gulf Cooperation Council)')),
        ('global', _('Global')),
    ]
    
    startup = models.ForeignKey(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='competitors',
        help_text=_("The startup this competitor is associated with")
    )
    
    competitor_type = models.CharField(
        max_length=10,
        choices=COMPETITOR_TYPE_CHOICES,
        help_text=_("Type of competitor (Local, GCC, or Global)")
    )
    
    competitor_name = models.CharField(
        max_length=255,
        help_text=_("Name of the competitor company")
    )
    
    competitor_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Competitor's website URL")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Description of the competitor and their business")
    )
    
    market_share = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Estimated market share percentage")
    )
    
    funding_raised = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Total funding raised by competitor")
    )
    
    founded_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Year the competitor was founded")
    )
    
    employee_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Number of employees")
    )
    
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Competitor's headquarters location")
    )
    
    strengths = models.TextField(
        blank=True,
        help_text=_("Competitor's key strengths")
    )
    
    weaknesses = models.TextField(
        blank=True,
        help_text=_("Competitor's weaknesses or gaps")
    )
    
    threat_level = models.CharField(
        max_length=10,
        choices=[
            ('high', _('High')),
            ('medium', _('Medium')),
            ('low', _('Low')),
        ],
        default='medium',
        help_text=_("Level of competitive threat")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this competitor is still active")
    )
    
    class Meta:
        verbose_name = _("Competitor")
        verbose_name_plural = _("Competitors")
        db_table = "competitor"
        ordering = ['-threat_level', 'competitor_type', 'competitor_name']
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['competitor_type']),
            models.Index(fields=['threat_level']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.competitor_name} ({self.get_competitor_type_display()})"
    
    @property
    def funding_raised_formatted(self):
        """Return formatted funding amount."""
        if self.funding_raised:
            if self.funding_raised >= 1_000_000_000:
                return f"${self.funding_raised / 1_000_000_000:.2f}B"
            elif self.funding_raised >= 1_000_000:
                return f"${self.funding_raised / 1_000_000:.2f}M"
            elif self.funding_raised >= 1_000:
                return f"${self.funding_raised / 1_000:.2f}K"
            else:
                return f"${self.funding_raised:.2f}"
        return None
    
    @property
    def age_years(self):
        """Calculate the age of the competitor in years."""
        if self.founded_year:
            from datetime import date
            current_year = date.today().year
            return current_year - self.founded_year
        return None

