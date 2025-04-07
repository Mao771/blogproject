from django.db.models.signals import post_save, post_delete
from django.core.cache import cache
import logging
from .events import PostProducer
import os

from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import BlogPost

logger = logging.getLogger("django")


@receiver(m2m_changed, sender=BlogPost.likes.through)
def update_like_count(sender, instance, **kwargs):
    logger.info("m2m_changed")
    cache.delete_pattern("*blogpost*")


@receiver([post_save, post_delete], sender=BlogPost, dispatch_uid="BlogPostSignal")
def invalidate_blogpost_cache(sender, instance, **kwargs):
    cache.delete_pattern("*blogpost*")
    created = kwargs.get("created")
    logger.info(f"CREATED {created}")

    if created:
        logger.info(f"Post {instance.id} created. Sending event to RabbitMQ")
        try:
            post_producer = PostProducer()
            post_uri = os.environ['FRONTEND_URL'] + '/posts/' + str(instance.id)
            post_producer.send_event(instance.author, instance.id, post_uri)
            post_producer.close()
        except Exception as e:
            logger.error("Failed to produce event on post creation. Error: %s" % e)
