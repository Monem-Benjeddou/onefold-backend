from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class Stakeholder(AbstractAutoIncrementModel):
    """
    Stakeholders in a startup including investors, advisors, partners, suppliers, and members.
    """
    
    STAKEHOLDER_TYPE_CHOICES = [
        ('investor', _('Investor')),
        ('advisor', _('Advisor')),
        ('partner', _('Partner')),
        ('supplier', _('Supplier')),
        ('member', _('Member')),
        ('customer', _('Customer')),
        ('vendor', _('Vendor')),
        ('other', _('Other')),
    ]
    
    INFLUENCE_LEVEL_CHOICES = [
        ('high', _('High')),
        ('medium', _('Medium')),
        ('low', _('Low')),
    ]
    
    STAKE_LEVEL_CHOICES = [
        ('high', _('High')),
        ('medium', _('Medium')),
        ('low', _('Low')),
    ]
    
    startup = models.ForeignKey(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='stakeholders',
        help_text=_("The startup this stakeholder is associated with")
    )
    
    full_name = models.CharField(
        max_length=255,
        help_text=_("Full name of the stakeholder")
    )
    
    stakeholder_type = models.CharField(
        max_length=20,
        choices=STAKEHOLDER_TYPE_CHOICES,
        help_text=_("Type of stakeholder")
    )
    
    role_title = models.CharField(
        max_length=255,
        help_text=_("Role or title in relation to the startup")
    )
    
    influence_level = models.CharField(
        max_length=10,
        choices=INFLUENCE_LEVEL_CHOICES,
        help_text=_("How influential they are in the startup")
    )
    
    stake_interest_level = models.CharField(
        max_length=10,
        choices=STAKE_LEVEL_CHOICES,
        help_text=_("Their stake/interest level in the startup")
    )
    
    ownership_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Percentage of ownership or shares (if investor/partner)")
    )
    
    investment_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Amount invested (if applicable)")
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
    
    company_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Company name (if stakeholder represents a company)")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Additional description or notes about the stakeholder")
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this stakeholder relationship is currently active")
    )
    
    class Meta:
        verbose_name = _("Stakeholder")
        verbose_name_plural = _("Stakeholders")
        db_table = "stakeholder"
        ordering = ['-influence_level', 'stakeholder_type', 'full_name']
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['stakeholder_type']),
            models.Index(fields=['influence_level']),
            models.Index(fields=['stake_interest_level']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.get_stakeholder_type_display()}"
    
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

