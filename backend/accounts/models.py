from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    username = models.CharField(max_length=30, unique=True, validators=[RegexValidator(
        r"^[A-Za-z0-9_]{3,30}$", "Только латиница, цифры и _, от 3 до 30 символов",
    )])
    email = models.EmailField(unique=True, max_length=254)

    class Meta:
        db_table = "users"
        constraints = [models.UniqueConstraint(Lower("email"), name="unique_email_lower")]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def role(self):
        return "admin" if self.is_staff else "user"


class RevokedToken(models.Model):
    jti = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
