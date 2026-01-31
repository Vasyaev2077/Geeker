from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from apps.core.models import TimeStampedModel


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Collection(TimeStampedModel):
    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        FRIENDS = "friends", "Friends"
        PUBLIC = "public", "Public"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="collections",
        db_index=True,
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
        db_index=True,
    )
    tags = models.ManyToManyField(Tag, related_name="collections", blank=True)
    is_archived = models.BooleanField(default=False, db_index=True)

    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "visibility"]),
            GinIndex(fields=["search_vector"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.owner})"


class Section(models.Model):
    """
    Раздел библиотеки (Фильмы, Видеоигры, Комиксы и т.п.).
    Может использоваться для фильтрации предметов.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, db_index=True)
<<<<<<< HEAD
    description = models.CharField(max_length=50, blank=True)
    cover = models.ImageField(upload_to="sections/", blank=True, null=True)

    # Internal mapping: each Section owns a single Collection (hidden in UI)
    collection = models.OneToOneField(
        "Collection",
        on_delete=models.CASCADE,
        related_name="section",
        null=True,
        blank=True,
    )
=======
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753

    class Meta:
        unique_together = ("owner", "slug")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
<<<<<<< HEAD
        # IMPORTANT: allow unicode so Cyrillic doesn't collapse to empty slug.
        # Also ensure uniqueness per owner (unique_together owner+slug).
        if not self.slug:
            base = slugify(self.name, allow_unicode=True) or "section"
            candidate = base
            n = 2
            while Section.objects.filter(owner=self.owner, slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{n}"
                n += 1
            self.slug = candidate
=======
        if not self.slug:
            self.slug = slugify(self.name)
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753
        super().save(*args, **kwargs)


class Item(TimeStampedModel):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="items",
        db_index=True,
    )
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, related_name="items", blank=True)
    sections = models.ManyToManyField("Section", related_name="items", blank=True)
    metadata = models.JSONField(blank=True, default=dict)
    position = models.PositiveIntegerField(default=0, db_index=True)

    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        ordering = ["position", "-created_at"]
        indexes = [
            models.Index(fields=["collection", "position"]),
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self) -> str:
        return self.title

    def set_position_to_end(self):
        max_pos = (
            Item.objects.filter(collection=self.collection)
            .aggregate(models.Max("position"))
            .get("position__max")
            or 0
        )
        self.position = max_pos + 1


class ItemMedia(TimeStampedModel):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        FILE = "file", "File"

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="media",
        db_index=True,
    )
    file = models.FileField(upload_to="items/")
    type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
    )
    is_primary = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
<<<<<<< HEAD
        # Always show cover first, then keep user's order
        ordering = ["-is_primary", "position", "id"]
=======
        ordering = ["position"]
>>>>>>> c3b89d27ec563af11f9e50443796471accc02753
        indexes = [
            models.Index(fields=["item", "position"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} for {self.item}"







