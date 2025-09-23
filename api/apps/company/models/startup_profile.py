from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.abstract.models import AbstractAutoIncrementModel
from apps.accounts.user.models import User


def startup_logo_path(instance, filename):
    return f"startups/{instance.id}/logo/{filename}"


def startup_pitch_deck_path(instance, filename):
    return f"startups/{instance.id}/pitch_deck/{filename}"


class StartupProfile(AbstractAutoIncrementModel):
    """
    Main startup/company profile containing core business information.
    """
    
    # Core Information
    startup_name = models.CharField(
        max_length=255,
        help_text=_("Name of the startup/company")
    )
    
    startup_industry = models.CharField(
        max_length=100,
        help_text=_("Industry or sector of the startup")
    )
    
    website_link = models.URLField(
        blank=True,
        null=True,
        help_text=_("Company website URL")
    )
    
    location = models.CharField(
        max_length=255,
        help_text=_("Headquarters location or remote status")
    )
    
    founded_year = models.PositiveIntegerField(
        help_text=_("Year the company was founded")
    )
    
    # Business Information
    bio = models.TextField(
        blank=True,
        help_text=_("Company description and mission")
    )
    
    
    # Social Media Links
    linkedin_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Company LinkedIn page URL")
    )
    
    twitter_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Company Twitter profile URL")
    )
    
    facebook_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Company Facebook page URL")
    )
    
    instagram_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Company Instagram profile URL")
    )
    
    youtube_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Company YouTube channel URL")
    )
    
    # Media and Documents
    logo = models.ImageField(
        upload_to=startup_logo_path,
        null=True,
        blank=True,
        help_text=_("Company logo")
    )
    
    pitch_deck_link = models.URLField(
        blank=True,
        null=True,
        help_text=_("Link to pitch deck presentation")
    )
    
    pitch_deck_file = models.FileField(
        upload_to=startup_pitch_deck_path,
        null=True,
        blank=True,
        help_text=_("Pitch deck file upload")
    )
    
    # Status and Verification
    is_verified = models.BooleanField(
        default=False,
        help_text=_("Whether this startup profile is verified")
    )
    
    is_public = models.BooleanField(
        default=True,
        help_text=_("Whether this profile is publicly visible")
    )   
    
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether the startup is currently active")
    )
    
    primary_founder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_startups',
        help_text=_("Primary founder of the startup")
    )
    
    class Meta:
        app_label = "company"
        verbose_name = _("Startup Profile")
        verbose_name_plural = _("Startup Profiles")
        db_table = "startup_profile"
        indexes = [
            models.Index(fields=['startup_name']),
            models.Index(fields=['startup_industry']),
            models.Index(fields=['founded_year']),
            models.Index(fields=['location']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_public']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.startup_name} ({self.startup_industry})"
    
    @property
    def social_links(self):
        """Return a dictionary of all social media links."""
        return {
            'linkedin': self.linkedin_url,
            'twitter': self.twitter_url,
            'facebook': self.facebook_url,
            'instagram': self.instagram_url,
            'youtube': self.youtube_url,
        }
    
    def get_active_social_links(self):
        """Return only non-empty social media links."""
        return {k: v for k, v in self.social_links.items() if v}
    
    @property
    def age_years(self):
        """Calculate the age of the startup in years."""
        from datetime import date
        current_year = date.today().year
        return current_year - self.founded_year


class StartupServiceProduct(AbstractAutoIncrementModel):
    """
    Discrete service/product offered by a startup.
    One-to-many: each service/product belongs to one StartupProfile.
    """

    startup = models.ForeignKey(
        StartupProfile,
        on_delete=models.CASCADE,
        related_name="services_and_products",
        help_text=_("Related startup profile"),
    )
    name = models.CharField(max_length=255, help_text=_("Service/Product name"))
    description = models.TextField(blank=True, help_text=_("Optional description"))
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "company"
        verbose_name = _("Startup Service/Product")
        verbose_name_plural = _("Startup Services/Products")
        db_table = "startup_service_product"
        indexes = [
            models.Index(fields=["startup", "is_active"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.startup.startup_name})"

