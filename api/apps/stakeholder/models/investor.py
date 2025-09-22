from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class Investor(AbstractAutoIncrementModel):
    """
    Detailed investor information for startups.
    """
    
    INVESTMENT_TYPE_CHOICES = [
        ('angel', _('Angel Investment')),
        ('seed', _('Seed Funding')),
        ('series_a', _('Series A')),
        ('series_b', _('Series B')),
        ('series_c', _('Series C')),
        ('series_d', _('Series D')),
        ('mezzanine', _('Mezzanine')),
        ('ipo', _('IPO')),
        ('debt', _('Debt Financing')),
        ('grant', _('Grant')),
        ('other', _('Other')),
    ]
    
    startup = models.ForeignKey(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='investors',
        help_text=_("The startup this investor is associated with")
    )
    
    person_company_name = models.CharField(
        max_length=255,
        help_text=_("Name of the person or company making the investment")
    )
    
    address = models.TextField(
        blank=True,
        help_text=_("Address of the investor")
    )
    
    contact_email = models.EmailField(
        blank=True,
        null=True,
        help_text=_("Contact email address")
    )
    
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Contact phone number")
    )
    
    website = models.URLField(
        blank=True,
        null=True,
        help_text=_("Investor's website URL")
    )
    
    equity_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Percentage of equity received")
    )
    
    investment_type = models.CharField(
        max_length=20,
        choices=INVESTMENT_TYPE_CHOICES,
        help_text=_("Type of investment made")
    )
    
    investment_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Amount invested")
    )
    
    investment_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date of investment")
    )
    
    is_lead_investor = models.BooleanField(
        default=False,
        help_text=_("Whether this investor is the lead investor")
    )
    
    board_seat = models.BooleanField(
        default=False,
        help_text=_("Whether this investor has a board seat")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Additional notes about the investor")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this investment is currently active")
    )
    
    class Meta:
        verbose_name = _("Investor")
        verbose_name_plural = _("Investors")
        db_table = "investor"
        ordering = ['-investment_date', '-investment_amount', 'person_company_name']
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['investment_type']),
            models.Index(fields=['investment_date']),
            models.Index(fields=['is_lead_investor']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.person_company_name} - {self.get_investment_type_display()}"
    
    @property
    def investment_amount_formatted(self):
        """Return formatted investment amount."""
        if self.investment_amount:
            if self.investment_amount >= 1_000_000_000:
                return f"${self.investment_amount / 1_000_000_000:.2f}B"
            elif self.investment_amount >= 1_000_000:
                return f"${self.investment_amount / 1_000_000:.2f}M"
            elif self.investment_amount >= 1_000:
                return f"${self.investment_amount / 1_000:.2f}K"
            else:
                return f"${self.investment_amount:.2f}"
        return None

