from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        MODERATOR = "moderator", "Moderator"
        ADMIN = "admin", "Admin"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=150, db_index=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)
    language = models.CharField(
        max_length=5,
        choices=[("ru", "Russian"), ("en", "English")],
        default="ru",
    )
    timezone = models.CharField(max_length=64, default="Europe/Moscow")
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.USER,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
        ]

    def __str__(self) -> str:
        return self.display_name or self.user.username

    @property
    def is_moderator(self) -> bool:
        return self.role in {self.Role.MODERATOR, self.Role.ADMIN}

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN








