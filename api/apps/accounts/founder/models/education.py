from django.db import models
from django.utils.translation import gettext_lazy as _
from core.abstract.models import AbstractAutoIncrementModel
from apps.accounts.user.models import User


class Education(AbstractAutoIncrementModel):
    """
    Education history for founders.
    """
    
    founder = models.ForeignKey(
        'founder.FounderProfile',
        on_delete=models.CASCADE,
        related_name='education_history',
        help_text=_("The founder this education record belongs to")
    )
    
    institution_name = models.CharField(
        max_length=255,
        help_text=_("Name of the educational institution")
    )
    
    degree = models.CharField(
        max_length=255,
        help_text=_("Degree obtained (e.g., Bachelor of Science, MBA, PhD)")
    )
    
    field_of_study = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Field of study or major")
    )
    
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Start date of education")
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("End date or graduation date")
    )
    
    is_current = models.BooleanField(
        default=False,
        help_text=_("Whether currently enrolled")
    )
    
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Grade Point Average if applicable")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Additional details about the education")
    )
    
    institution_website = models.URLField(
        blank=True,
        null=True,
        help_text=_("Institution's website URL")
    )
    
    class Meta:
        app_label = "founder"
        verbose_name = _("Education")
        verbose_name_plural = _("Education Records")
        db_table = "founder_education"
        ordering = ['-end_date', '-start_date']
        indexes = [
            models.Index(fields=['founder']),
            models.Index(fields=['institution_name']),
            models.Index(fields=['degree']),
        ]
    
    def __str__(self):
        return f"{self.degree} from {self.institution_name}"
    
    @property
    def duration(self):
        """Calculate the duration of education."""
        if self.start_date and self.end_date:
            return self.end_date - self.start_date
        return None
    
    @property
    def is_completed(self):
        """Check if education is completed."""
        return self.end_date is not None and not self.is_current

