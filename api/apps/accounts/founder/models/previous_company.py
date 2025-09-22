from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel


class PreviousCompany(AbstractAutoIncrementModel):
    """
    Previous companies or startups that the founder has worked at.
    """
    
    founder = models.ForeignKey(
        'founder.FounderProfile',
        on_delete=models.CASCADE,
        related_name='previous_companies',
        help_text=_("The founder this company record belongs to")
    )
    
    company_name = models.CharField(
        max_length=255,
        help_text=_("Name of the company or startup")
    )
    
    profile_link = models.URLField(
        blank=True,
        null=True,
        help_text=_("Link to company profile or website")
    )
    
    position = models.CharField(
        max_length=255,
        help_text=_("Position or role held at the company")
    )
    
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Start date of employment")
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("End date of employment")
    )
    
    is_current = models.BooleanField(
        default=False,
        help_text=_("Whether currently working at this company")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Description of role and achievements")
    )
    
    company_type = models.CharField(
        max_length=50,
        choices=[
            ('startup', _('Startup')),
            ('corporation', _('Corporation')),
            ('non_profit', _('Non-Profit')),
            ('government', _('Government')),
            ('consulting', _('Consulting')),
            ('other', _('Other')),
        ],
        default='startup',
        help_text=_("Type of company")
    )
    
    industry = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Industry or sector of the company")
    )
    
    company_size = models.CharField(
        max_length=20,
        choices=[
            ('1-10', _('1-10 employees')),
            ('11-50', _('11-50 employees')),
            ('51-200', _('51-200 employees')),
            ('201-500', _('201-500 employees')),
            ('501-1000', _('501-1000 employees')),
            ('1000+', _('1000+ employees')),
        ],
        blank=True,
        help_text=_("Size of the company")
    )
    
    class Meta:
        app_label = "founder"
        verbose_name = _("Previous Company")
        verbose_name_plural = _("Previous Companies")
        db_table = "founder_previous_company"
        ordering = ['-end_date', '-start_date']
        indexes = [
            models.Index(fields=['founder']),
            models.Index(fields=['company_name']),
            models.Index(fields=['company_type']),
            models.Index(fields=['industry']),
        ]
    
    def __str__(self):
        return f"{self.position} at {self.company_name}"
    
    @property
    def duration(self):
        """Calculate the duration of employment."""
        if self.start_date and self.end_date:
            return self.end_date - self.start_date
        return None
    
    @property
    def is_completed(self):
        """Check if employment is completed."""
        return self.end_date is not None and not self.is_current

