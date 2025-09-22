from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class RaisedFund(AbstractAutoIncrementModel):
    """
    Records of funds raised by startups.
    """
    
    startup = models.ForeignKey(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='raised_funds',
        help_text=_("The startup that raised these funds")
    )
    
    amount_raised = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text=_("Amount of funds raised")
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
            ('debt', _('Debt Financing')),
            ('grant', _('Grant')),
            ('other', _('Other')),
        ],
        help_text=_("Funding round type")
    )
    
    funding_date = models.DateField(
        help_text=_("Date when the funding was raised")
    )
    
    lead_investor = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Name of the lead investor")
    )
    
    participating_investors = models.TextField(
        blank=True,
        help_text=_("List of all participating investors")
    )
    
    pre_money_valuation = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Pre-money valuation at the time of funding")
    )
    
    post_money_valuation = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Post-money valuation after funding")
    )
    
    equity_offered = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Percentage of equity offered in this round")
    )
    
    use_of_funds = models.TextField(
        blank=True,
        help_text=_("How the raised funds will be used")
    )
    
    is_announced = models.BooleanField(
        default=False,
        help_text=_("Whether this funding round has been publicly announced")
    )
    
    announcement_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date when the funding was announced")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Additional details about the funding round")
    )
    
    class Meta:
        verbose_name = _("Raised Fund")
        verbose_name_plural = _("Raised Funds")
        db_table = "raised_fund"
        ordering = ['-funding_date', '-amount_raised']
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['funding_round']),
            models.Index(fields=['funding_date']),
            models.Index(fields=['is_announced']),
        ]
    
    def __str__(self):
        return f"{self.startup.startup_name} - {self.get_funding_round_display()} - {self.amount_raised_formatted}"
    
    def save(self, *args, **kwargs):
        """Calculate post-money valuation if both amount raised and pre-money valuation are set."""
        if self.amount_raised and self.pre_money_valuation:
            self.post_money_valuation = self.pre_money_valuation + self.amount_raised
        super().save(*args, **kwargs)
    
    @property
    def amount_raised_formatted(self):
        """Return formatted amount raised."""
        if self.amount_raised:
            if self.amount_raised >= 1_000_000_000:
                return f"${self.amount_raised / 1_000_000_000:.2f}B"
            elif self.amount_raised >= 1_000_000:
                return f"${self.amount_raised / 1_000_000:.2f}M"
            elif self.amount_raised >= 1_000:
                return f"${self.amount_raised / 1_000:.2f}K"
            else:
                return f"${self.amount_raised:.2f}"
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

