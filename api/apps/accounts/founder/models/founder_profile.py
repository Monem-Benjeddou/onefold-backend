from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from core.abstract.models import AbstractAutoIncrementModel


def founder_avatar_path(instance, filename):
    return f"founders/{instance.user.id}/avatar/{filename}"


def founder_background_path(instance, filename):
    return f"founders/{instance.user.id}/background/{filename}"


class FounderProfile(AbstractAutoIncrementModel):
    """
    Extended profile for founder users containing startup-specific information.
    """
    
    # Core founder information
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='founder_profile',
        help_text=_("The user account associated with this founder profile")
    )
    
    # Basic Information
    full_name = models.CharField(
        max_length=255,
        help_text=_("Full name of the founder")
    )
    
    email_address = models.EmailField(
        help_text=_("Primary email address for business communications")
    )
    
    ROLE_CHOICES = [
        ('ceo', _('CEO - Chief Executive Officer')),
        ('cto', _('CTO - Chief Technology Officer')),
        ('cmo', _('CMO - Chief Marketing Officer')),
        ('cfo', _('CFO - Chief Financial Officer')),
        ('coo', _('COO - Chief Operating Officer')),
        ('cpo', _('CPO - Chief Product Officer')),
        ('cso', _('CSO - Chief Strategy Officer')),
        ('founder', _('Founder')),
        ('co_founder', _('Co-Founder')),
        ('other', _('Other')),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text=_("Role/position in the startup")
    )
    
    location = models.CharField(
        max_length=255,
        help_text=_("Base city or location")
    )
    
    birthdate = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date of birth")
    )
    
    # Social Media Links
    linkedin_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("LinkedIn profile URL")
    )
    
    twitter_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Twitter profile URL")
    )
    
    facebook_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Facebook profile URL")
    )
    
    instagram_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Instagram profile URL")
    )
    
    github_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("GitHub profile URL")
    )
    
    personal_website = models.URLField(
        blank=True,
        null=True,
        help_text=_("Personal website URL")
    )
    
    # Bio and Media
    bio = models.TextField(
        blank=True,
        help_text=_("Founder's biography and background")
    )
    
    avatar = models.ImageField(
        upload_to=founder_avatar_path,
        null=True,
        blank=True,
        help_text=_("Founder's profile picture")
    )
    
    background_image = models.ImageField(
        upload_to=founder_background_path,
        null=True,
        blank=True,
        help_text=_("Background image for founder profile")
    )
    
    # Verification and Status
    is_verified = models.BooleanField(
        default=False,
        help_text=_("Whether this founder profile is verified")
    )
    
    is_public = models.BooleanField(
        default=True,
        help_text=_("Whether this profile is publicly visible")
    )
    
    class Meta:
        app_label = "founder"
        verbose_name = _("Founder Profile")
        verbose_name_plural = _("Founder Profiles")
        db_table = "founder_profile"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
            models.Index(fields=['location']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.full_name} - {self.get_role_display()}"
    
    @property
    def social_links(self):
        """Return a dictionary of all social media links."""
        return {
            'linkedin': self.linkedin_url,
            'twitter': self.twitter_url,
            'facebook': self.facebook_url,
            'instagram': self.instagram_url,
            'github': self.github_url,
            'website': self.personal_website,
        }
    
    def get_active_social_links(self):
        """Return only non-empty social media links."""
        return {k: v for k, v in self.social_links.items() if v}

