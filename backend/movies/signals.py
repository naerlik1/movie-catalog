from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from pathlib import Path
from .models import MovieFile


@receiver(post_delete, sender=MovieFile)
def remove_poster(sender, instance, **kwargs):
    path = Path(settings.MEDIA_ROOT) / "public" / instance.stored_name
    transaction.on_commit(lambda: path.unlink(missing_ok=True))
