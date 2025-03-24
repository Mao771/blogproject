from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from webapp.models import BlogPost
from django.core.cache import cache


@receiver([post_save, post_delete], sender=BlogPost)
def invalidate_blogpost_cache(sender, instance, **kwargs):
    cache.delete_pattern('*blogpost*')
