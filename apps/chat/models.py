from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class Chat(TimeStampedModel):
    class ChatType(models.TextChoices):
        DIRECT = "direct", "Direct"
        GROUP = "group", "Group"
        COMMUNITY = "community", "Community"

    type = models.CharField(
        max_length=16,
        choices=ChatType.choices,
        default=ChatType.DIRECT,
        db_index=True,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="chats",
        blank=True,
    )
    community = models.ForeignKey(
        "communities.Community",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="chats",
    )

    class Meta:
        indexes = [
            models.Index(fields=["type"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} chat #{self.pk}"


class Message(TimeStampedModel):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    text = models.TextField()
    attachments = models.JSONField(blank=True, default=list)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["chat", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Message #{self.pk} in chat {self.chat_id}"








