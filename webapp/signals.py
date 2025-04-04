from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from webapp.models import BlogPost
from django.core.cache import cache
import logging
from .events import PostProducer
import os

logger = logging.getLogger("django")


@receiver([post_save, post_delete], sender=BlogPost, dispatch_uid="BlogPostSignal")
def invalidate_blogpost_cache(sender, instance, **kwargs):
    cache.delete_pattern("*blogpost*")
    created = kwargs.get("created")

    if created:
        logger.info(f"Post {instance.id} created. Sending event to RabbitMQ")
        try:
            post_producer = PostProducer()
            post_uri = os.environ['FRONTEND_URL'] + '/posts/' + str(instance.id)
            post_producer.send_event(instance.author, instance.id, post_uri)
            post_producer.close()
        except Exception as e:
            logger.error("Failed to produce event on post creation. Error: %s" % e)
