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


class ProfilePost(TimeStampedModel):
    """
    Пост в профиле пользователя (лента как в соцсети).
    Поддерживает закрепление, отключение комментариев и удаление.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile_posts",
        db_index=True,
    )
    text = models.TextField(blank=True)
    media = models.FileField(upload_to="profile_posts/", blank=True, null=True)

    is_pinned = models.BooleanField(default=False, db_index=True)
    comments_enabled = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]
        indexes = [
            models.Index(fields=["author", "is_deleted", "is_pinned", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Post #{self.pk} by {self.author}"

    @property
    def is_video(self) -> bool:
        if not self.media:
            return False
        name = (self.media.name or "").lower()
        return name.endswith((".mp4", ".webm", ".ogg", ".mov"))


class ProfilePostMedia(TimeStampedModel):
    """
    Медиафайлы поста (до 8 изображений).
    """

    post = models.ForeignKey(
        ProfilePost,
        on_delete=models.CASCADE,
        related_name="media_items",
        db_index=True,
    )
    file = models.ImageField(upload_to="profile_posts/", db_index=False)
    position = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["position", "created_at"]
        indexes = [
            models.Index(fields=["post", "position"]),
        ]

    def __str__(self) -> str:
        return f"Media for post {self.post_id} ({self.position})"


class ProfilePostVote(TimeStampedModel):
    class Value(models.IntegerChoices):
        DOWN = -1, "Down"
        UP = 1, "Up"

    post = models.ForeignKey(
        ProfilePost,
        on_delete=models.CASCADE,
        related_name="votes",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile_post_votes",
        db_index=True,
    )
    value = models.SmallIntegerField(choices=Value.choices, db_index=True)

    class Meta:
        unique_together = ("post", "user")
        indexes = [
            models.Index(fields=["post", "value"]),
        ]


class ProfilePostComment(TimeStampedModel):
    post = models.ForeignKey(
        ProfilePost,
        on_delete=models.CASCADE,
        related_name="comments",
        db_index=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile_post_comments",
        db_index=True,
    )
    text = models.TextField()
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "created_at"]),
        ]








