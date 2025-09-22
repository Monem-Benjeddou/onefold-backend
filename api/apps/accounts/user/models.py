import random
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.utils.translation import gettext as _
from django.db import models
from django.conf import settings
from core.abstract.models import AbstractAutoIncrementModel
from .managers import UserManager, VerificationCodeManager
from .constants import ROLE_CHOICES


def user_directory_path(instance, filename):
    return "user_{0}/{1}".format(instance.id, filename)


class User(AbstractAutoIncrementModel, AbstractBaseUser, PermissionsMixin):
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    username = models.CharField(db_index=True, max_length=255, unique=True)
    email = models.EmailField(
        db_index=True, unique=True, max_length=255, blank=True, null=True
    )
    fullname = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(
        default=True, help_text="Whether the user account is active"
    )
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_verified = models.BooleanField(
        default=False,
        help_text=_("Whether this user is verified (blue check mark for influencers)"),
    )
    avatar = models.ImageField(null=True, blank=True, upload_to=user_directory_path)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    date_of_birth = models.DateField(
        blank=True, null=True, help_text="User's date of birth"
    )
    gender = models.CharField(
        max_length=20,
        choices=[
            ("male", _("Male")),
            ("female", _("Female")),
        ],
        blank=True,
        null=True,
        help_text="User's gender",
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="user", db_index=True
    )
    country = models.ForeignKey(
        "countries.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    is_banned = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the user is temporarily banned from logging in",
    )
    ban_reason = models.TextField(
        blank=True, null=True, help_text="Reason for banning the user"
    )
    banned_at = models.DateTimeField(
        blank=True, null=True, help_text="When the user was banned"
    )
    banned_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="banned_users",
        help_text="Admin user who banned this user",
    )
    ban_expires_at = models.DateTimeField(
        blank=True, null=True, help_text="When the ban expires (null for permanent ban)"
    )

    is_deactivated = models.BooleanField(
        default=False, help_text="Whether the user account is deactivated"
    )
    deactivated_at = models.DateTimeField(
        blank=True, null=True, help_text="When the user account was deactivated"
    )
    deactivation_reason = models.TextField(
        blank=True, null=True, help_text="Reason for account deactivation"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["fullname"]

    objects: UserManager = UserManager()

    def __str__(self):
        return f"{self.email}" or f"{self.fullname}"

    def has_perm(self, perm, obj=None):
        """
        Enhanced permission checking that integrates Django Groups with object-level permissions.

        This method extends Django's standard permission checking to include:
        - Standard Django Groups permissions
        - Object-level permission validation
        - Superuser privilege override

        Args:
            perm: Permission string in format 'app_label.action_modelname'
            obj: Optional object for object-level permission checks

        Returns:
            bool: True if user has permission
        """

        if self.is_superuser:
            return True

        from .rbac import check_permission

        return check_permission(self, perm, obj)

    def has_module_perms(self, app_label):
        """
        Check if user has any permissions for the given app.

        Superusers have access to all modules. Regular users are checked
        against their group permissions.
        """
        if self.is_superuser:
            return True

        return super().has_module_perms(app_label)

    def get_permission_context(self):
        """
        Get user's permission context for use in templates and APIs.

        Returns:
            dict: Dictionary containing user's groups and capabilities
        """

        from .rbac import get_user_permission_context

        return get_user_permission_context(self)

    def get_groups(self):
        """
        Get all Django Groups assigned to this user.

        Note: Groups are assigned explicitly via management commands,
        not automatically based on role field.

        Returns:
            QuerySet: User's assigned groups
        """
        return self.groups.all()

    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == "admin" or self.is_superuser

    def is_coach(self):
        """Check if user has coach role (legacy method)."""
        return self.role == "coach"

    def is_doctor(self):
        """Check if user has doctor role (legacy method)."""
        return self.role == "doctor"

    def is_moderator(self):
        """Check if user has moderator role (legacy method)."""
        return self.role == "moderator"

    @property
    def is_salesman(self):
        """Check if user has salesman role."""
        return self.role == "salesman"

    @property
    def is_issuer(self):
        """Check if user has issuer role."""
        return self.role == "issuer"

    @property
    def is_regular_user(self):
        """Check if user has regular user role (collector)."""
        return self.role in ["user", "collector"]

    def is_currently_banned(self):
        """
        Check if the user is currently banned.

        Returns:
            bool: True if user is banned and ban hasn't expired
        """
        if not self.is_banned:
            return False

        if not self.ban_expires_at:
            return True

        from django.utils import timezone

        return timezone.now() < self.ban_expires_at

    def deactivate_account(self, reason=None):
        """
        Deactivate the user account.

        Args:
            reason (str, optional): Reason for deactivation
        """
        from django.utils import timezone

        self.is_deactivated = True
        self.deactivated_at = timezone.now()
        if reason:
            self.deactivation_reason = reason
        self.save(
            update_fields=[
                "is_deactivated",
                "deactivated_at",
                "deactivation_reason",
                "updated",
            ]
        )

    def reactivate_account(self):
        """
        Reactivate the user account.
        """
        self.is_deactivated = False
        self.deactivated_at = None
        self.deactivation_reason = None
        self.save(
            update_fields=[
                "is_deactivated",
                "deactivated_at",
                "deactivation_reason",
                "updated",
            ]
        )

    def is_account_active(self):
        """
        Check if the user account is fully active (not banned, not deactivated).

        Returns:
            bool: True if account is active
        """
        return not self.is_deactivated and not self.is_currently_banned()

    @property
    def full_name(self):
        return self.fullname or self.username

    def generate_verification_code(self, purpose="login"):
        """
        Generate an OTP verification code for the user.
        Clears any existing OTPs for the same purpose and creates a new one.

        Args:
            purpose (str): The purpose of the OTP ("login", "registration", "password_reset", "verification")

        Returns:
            str: The generated 6-digit OTP code
        """
        from apps.accounts.auth.models import OTP
        from apps.accounts.auth.utils import generate_otp
        from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
        from django.utils import timezone

        code = generate_otp()

        delivery_method = OTPDeliveryService.get_delivery_method()

        if delivery_method == "sms":
            if not self.phone_number and self.email:
                delivery_method = "fallback"

        OTP.objects.filter(user=self, purpose=purpose).delete()

        OTP.objects.create(
            user=self,
            code=code,
            purpose=purpose,
            delivery_method=delivery_method,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        return code

    def get_or_generate_verification_code(self, purpose="verification"):
        """
        Get existing valid OTP verification code for the user, or generate a new one if none exists.
        This method ensures users always have one valid OTP by reusing existing non-expired OTPs.

        Args:
            purpose (str): The purpose of the OTP ("login", "registration", "password_reset", "verification")

        Returns:
            str: The 6-digit OTP code (existing or newly generated)
        """
        from apps.accounts.auth.models import OTP
        from apps.accounts.auth.utils import generate_otp
        from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService
        from django.utils import timezone

        existing_otp = (
            OTP.objects.filter(user=self, purpose=purpose, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if existing_otp and existing_otp.is_valid():

            return existing_otp.code

        code = generate_otp()
        delivery_method = OTPDeliveryService.get_delivery_method()

        if delivery_method == "sms":
            if not self.phone_number and self.email:
                delivery_method = "fallback"


        OTP.objects.filter(user=self, purpose=purpose).delete()

        OTP.objects.create(
            user=self,
            code=code,
            purpose=purpose,
            delivery_method=delivery_method,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        return code

    def verify_code(self, code):
        """
        Verify if the provided OTP code is valid for this user.
        Marks the OTP as used after successful verification.

        Args:
            code (str): The OTP code to verify

        Returns:
            bool: True if OTP is valid and not used, False otherwise
        """
        from apps.accounts.auth.models import OTP
        from django.utils import timezone

        try:
            otp = OTP.objects.get(user=self, code=code)

            if not otp.is_valid():
                return False

            otp.mark_as_used()
            return True
        except OTP.DoesNotExist:
            return False

    def is_otp_valid(self, code):
        """
        Check if the provided OTP code is valid for this user without consuming it.
        This method does not mark the OTP as used, allowing for validation without state change.

        Args:
            code (str): The OTP code to validate

        Returns:
            bool: True if OTP exists, is not used, and is not expired, False otherwise
        """
        from apps.accounts.auth.models import OTP

        try:
            otp = OTP.objects.get(user=self, code=code)
            return otp.is_valid()
        except OTP.DoesNotExist:
            return False

    def verify_otp(self, code):
        """
        Verify and consume an OTP code for this user.
        This is an alias for verify_code for backward compatibility.

        Args:
            code (str): The OTP code to verify

        Returns:
            bool: True if OTP is valid and not used, False otherwise
        """
        return self.verify_code(code)

    def send_verification_email(self, email_type="verification"):
        """
        Send verification email to the user.

        This method is kept for backward compatibility but delegates OTP
        delivery to the new OTPDeliveryService for better flexibility.
        """
        if email_type in ["otp", "password_reset", "login"]:

            from apps.accounts.auth.models import OTP
            from apps.accounts.auth.services.otp_delivery_service import (
                OTPDeliveryService,
            )

            try:
                otp = OTP.objects.filter(user=self).latest("created_at")
                otp_type_mapping = {
                    "otp": "login",
                    "password_reset": "password_reset",
                    "login": "login",
                }
                return OTPDeliveryService.send_otp(
                    self, otp.code, otp_type_mapping.get(email_type, "login")
                )
            except OTP.DoesNotExist:
                return False
        else:

            from django.template.loader import render_to_string
            from django.utils.translation import gettext as _
            from core.tasks import send_activation_email

            verification_code = VerificationCode.objects.filter(user=self).first()
            if not verification_code:
                return False

            subject = _("Verify Your Email")
            text_content = _(f"Your verification code is: {verification_code.code}")
            html_content = render_to_string(
                "auth/emails/verification_code.html",
                {"code": verification_code.code, "user": self},
            )

            try:
                send_activation_email.delay(
                    subject=subject,
                    text_content=text_content,
                    html_content=html_content,
                    to_email=self.email,
                )
                return True
            except Exception:
                return False

    def send_otp(self, otp_type="login"):
        """
        Send OTP to user via configured delivery method (SMS or email).

        Args:
            otp_type: Type of OTP ("login", "password_reset", "verification")

        Returns:
            bool: True if OTP was sent successfully
        """
        from apps.accounts.auth.models import OTP
        from apps.accounts.auth.services.otp_delivery_service import OTPDeliveryService

        try:
            otp = OTP.objects.filter(user=self).latest("created_at")
            return OTPDeliveryService.send_otp(self, otp.code, otp_type)
        except OTP.DoesNotExist:
            return False
        except Exception:

            return False

    def _generate_username(self):
        """
        Generate a meaningful username based on available user data.
        Priority:
        1. Use fullname (cleaned and formatted)
        2. Use email prefix (part before @)
        3. Use full email as fallback

        Ensures uniqueness by appending numbers if needed.
        """
        import re

        base_username = None

        if self.fullname and self.fullname.strip():

            cleaned_name = re.sub(r"[^\w\s]", "", self.fullname.strip())
            base_username = re.sub(r"\s+", "_", cleaned_name.lower())

            if len(base_username) < 3:
                base_username = None

        if not base_username and self.email and "@" in self.email:
            email_prefix = self.email.split("@")[0]

            base_username = re.sub(r"[^\w.]", "_", email_prefix.lower())

        elif not base_username and self.email:

            base_username = re.sub(r"[@.]", "_", self.email.lower())
            base_username = re.sub(r"[^\w_]", "_", base_username)

        if not base_username:
            base_username = f"user_{random.randint(100000, 999999)}"

        if not base_username or len(base_username) < 3:
            base_username = f"user_{random.randint(100000, 999999)}"

        base_username = base_username[:140]

        username = base_username
        counter = 1

        try:
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

                if counter > 9999:
                    username = f"user_{random.randint(1000000, 9999999)}"
                    break
        except Exception:

            username = f"{base_username}_{random.randint(1000, 9999)}"

        return username

    def save(self, *args, **kwargs):
        """
        Enhanced save method for User model.

        Note: Group assignment is handled explicitly via management commands
        or admin interface, never automatically in model save methods.
        """

        if self.is_superuser:
            self.is_staff = True

        if not self.username or self.username.strip() == "":
            self.username = self._generate_username()

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "_user_user"
        permissions = [
            ("can_manage_user_roles", "Can manage user roles"),
            ("can_view_admin_stats", "Can view admin statistics"),
            ("can_moderate_all_content", "Can moderate all forum content"),
            ("can_access_api", "Can access API endpoints"),
        ]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
            models.Index(fields=["role"]),
            models.Index(fields=["created"]),
        ]


class VerificationCode(AbstractAutoIncrementModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)

    objects: VerificationCodeManager = VerificationCodeManager()

    @staticmethod
    def generate_code():
        return "".join(random.choices("0123456789", k=6))

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code}"

    class Meta:
        ordering = ["-created"]


class UserToken(AbstractAutoIncrementModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)

    class Meta:
        verbose_name = "User Token"
        verbose_name_plural = "User Tokens"
        indexes = [
            models.Index(fields=["token"]),
        ]
