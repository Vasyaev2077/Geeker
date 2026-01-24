from django.conf import settings
from django.db import models
from django.utils.text import slugify
from apps.core.models import TimeStampedModel


class Community(TimeStampedModel):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_communities",
    )
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        db_index=True,
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="CommunityMembership",
        related_name="communities",
    )

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class CommunityMembership(TimeStampedModel):
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        MODERATOR = "moderator", "Moderator"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True,
    )
    is_banned = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "community")
        indexes = [
            models.Index(fields=["community", "role"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} in {self.community} ({self.role})"








