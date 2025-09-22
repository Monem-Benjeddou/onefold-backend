from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class TargetedMarket(AbstractAutoIncrementModel):
    """
    Targeted markets for startups with market size and share information.
    """
    
    MARKET_TYPE_CHOICES = [
        ('local', _('Local')),
        ('gcc', _('GCC (Gulf Cooperation Council)')),
        ('global', _('Global')),
    ]
    
    startup = models.ForeignKey(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='targeted_markets',
        help_text=_("The startup this market belongs to")
    )
    
    market_type = models.CharField(
        max_length=10,
        choices=MARKET_TYPE_CHOICES,
        help_text=_("Type of market (Local, GCC, or Global)")
    )
    
    market_name = models.CharField(
        max_length=255,
        help_text=_("Name or description of the specific market")
    )
    
    market_size = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Total market size in USD")
    )
    
    market_share = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Percentage of market share targeted")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Description of the market opportunity")
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text=_("Whether this is the primary target market")
    )
    
    class Meta:
        app_label = "company"
        verbose_name = _("Targeted Market")
        verbose_name_plural = _("Targeted Markets")
        db_table = "targeted_market"
        ordering = ['-is_primary', 'market_type', 'market_name']
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['market_type']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.startup.startup_name} - {self.market_name} ({self.get_market_type_display()})"
    
    @property
    def market_size_formatted(self):
        """Return formatted market size."""
        if self.market_size:
            if self.market_size >= 1_000_000_000:
                return f"${self.market_size / 1_000_000_000:.2f}B"
            elif self.market_size >= 1_000_000:
                return f"${self.market_size / 1_000_000:.2f}M"
            elif self.market_size >= 1_000:
                return f"${self.market_size / 1_000:.2f}K"
            else:
                return f"${self.market_size:.2f}"
        return None

