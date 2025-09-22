from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class FundingTarget(AbstractAutoIncrementModel):
    """
    Funding targets and pre-money valuations for startups.
    """
    
    startup = models.OneToOneField(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='funding_target',
        help_text=_("The startup this funding target belongs to")
    )
    
    target_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Target funding amount to raise")
    )
    
    pre_money_valuation = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Pre-money valuation of the startup")
    )
    
    post_money_valuation = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Post-money valuation (calculated)")
    )
    
    funding_round = models.CharField(
        max_length=50,
        choices=[
            ('pre_seed', _('Pre-Seed')),
            ('seed', _('Seed')),
            ('series_a', _('Series A')),
            ('series_b', _('Series B')),
            ('series_c', _('Series C')),
            ('series_d', _('Series D')),
            ('mezzanine', _('Mezzanine')),
            ('ipo', _('IPO')),
        ],
        help_text=_("Current funding round")
    )
    
    use_of_funds = models.TextField(
        blank=True,
        help_text=_("How the funding will be used")
    )
    
    timeline = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Timeline for raising the funds")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this funding target is currently active")
    )
    
    class Meta:
        verbose_name = _("Funding Target")
        verbose_name_plural = _("Funding Targets")
        db_table = "funding_target"
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['funding_round']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.startup.startup_name} - {self.get_funding_round_display()}"
    
    def save(self, *args, **kwargs):
        """Calculate post-money valuation if both target amount and pre-money valuation are set."""
        if self.target_amount and self.pre_money_valuation:
            self.post_money_valuation = self.pre_money_valuation + self.target_amount
        super().save(*args, **kwargs)
    
    @property
    def target_amount_formatted(self):
        """Return formatted target amount."""
        if self.target_amount:
            if self.target_amount >= 1_000_000_000:
                return f"${self.target_amount / 1_000_000_000:.2f}B"
            elif self.target_amount >= 1_000_000:
                return f"${self.target_amount / 1_000_000:.2f}M"
            elif self.target_amount >= 1_000:
                return f"${self.target_amount / 1_000:.2f}K"
            else:
                return f"${self.target_amount:.2f}"
        return None
    
    @property
    def pre_money_valuation_formatted(self):
        """Return formatted pre-money valuation."""
        if self.pre_money_valuation:
            if self.pre_money_valuation >= 1_000_000_000:
                return f"${self.pre_money_valuation / 1_000_000_000:.2f}B"
            elif self.pre_money_valuation >= 1_000_000:
                return f"${self.pre_money_valuation / 1_000_000:.2f}M"
            elif self.pre_money_valuation >= 1_000:
                return f"${self.pre_money_valuation / 1_000:.2f}K"
            else:
                return f"${self.pre_money_valuation:.2f}"
        return None
    
    @property
    def post_money_valuation_formatted(self):
        """Return formatted post-money valuation."""
        if self.post_money_valuation:
            if self.post_money_valuation >= 1_000_000_000:
                return f"${self.post_money_valuation / 1_000_000_000:.2f}B"
            elif self.post_money_valuation >= 1_000_000:
                return f"${self.post_money_valuation / 1_000_000:.2f}M"
            elif self.post_money_valuation >= 1_000:
                return f"${self.post_money_valuation / 1_000:.2f}K"
            else:
                return f"${self.post_money_valuation:.2f}"
        return None

