from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.abstract.models import AbstractAutoIncrementModel


class CompanyMember(AbstractAutoIncrementModel):
    """
    Members of a startup company including founders and other team members.
    """
    
    MEMBER_TYPE_CHOICES = [
        ('founder', _('Founder')),
        ('co_founder', _('Co-Founder')),
        ('employee', _('Employee')),
        ('advisor', _('Advisor')),
        ('consultant', _('Consultant')),
        ('intern', _('Intern')),
        ('contractor', _('Contractor')),
    ]
    
    startup = models.ForeignKey(
        'company.StartupProfile',
        on_delete=models.CASCADE,
        related_name='members',
        help_text=_("The startup this member belongs to")
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_memberships',
        help_text=_("The user account of this member")
    )
    
    member_type = models.CharField(
        max_length=20,
        choices=MEMBER_TYPE_CHOICES,
        help_text=_("Type of membership in the company")
    )
    
    position = models.CharField(
        max_length=255,
        help_text=_("Position or role in the company")
    )
    
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Start date of membership")
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("End date of membership (if applicable)")
    )
    
    is_current = models.BooleanField(
        default=True,
        help_text=_("Whether currently a member of the company")
    )
    
    is_primary_contact = models.BooleanField(
        default=False,
        help_text=_("Whether this member is the primary contact for the company")
    )
    
    equity_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Percentage of equity owned (if applicable)")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Description of role and responsibilities")
    )
    
    class Meta:
        app_label = "company"
        verbose_name = _("Company Member")
        verbose_name_plural = _("Company Members")
        db_table = "company_member"
        unique_together = ['startup', 'user']
        ordering = ['-is_current', 'member_type', 'position']
        indexes = [
            models.Index(fields=['startup']),
            models.Index(fields=['user']),
            models.Index(fields=['member_type']),
            models.Index(fields=['is_current']),
            models.Index(fields=['is_primary_contact']),
        ]
    
    def __str__(self):
        return f"{self.user.fullname} - {self.position} at {self.startup.startup_name}"
    
    @property
    def duration(self):
        """Calculate the duration of membership."""
        if self.start_date and self.end_date:
            return self.end_date - self.start_date
        return None
    
    @property
    def is_founder(self):
        """Check if this member is a founder."""
        return self.member_type in ['founder', 'co_founder']

