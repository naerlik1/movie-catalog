from datetime import date
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models


def validate_year(value):
    if value < 1888 or value > date.today().year:
        raise ValidationError(f"Год должен быть от 1888 до {date.today().year}")


class Movie(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="movies")
    title = models.CharField("Название", max_length=120, validators=[MinLengthValidator(1)])
    year = models.PositiveSmallIntegerField("Год", validators=[validate_year])
    description = models.TextField("Описание", blank=True, max_length=2000, validators=[MaxLengthValidator(2000)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        db_table = "movies"

    def __str__(self):
        return f"{self.title} ({self.year})"

    def clean(self):
        self.title = self.title.strip()
        if not self.title:
            raise ValidationError({"title": "Введите название (до 120 символов)"})


class MovieFile(models.Model):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name="poster")
    original_name = models.CharField(max_length=255)
    stored_name = models.CharField(max_length=255, unique=True)
    mime = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "files"


class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    text = models.TextField(max_length=2000, validators=[MaxLengthValidator(2000)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["movie", "owner"], name="one_review_per_movie"),
            models.CheckConstraint(condition=models.Q(rating__gte=1, rating__lte=10), name="rating_1_to_10"),
        ]


class Favorite(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="favorites")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["movie", "owner"], name="unique_favorite")]


class Watched(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="watched_by")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watched_movies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["movie", "owner"], name="unique_watched")]
