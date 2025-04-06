import uuid
import imghdr

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from webapp.models import BlogPost


class Command(BaseCommand):
    help = "Migrate post_picture BinaryField to post_image ImageField"

    def handle(self, *args, **kwargs):
        updated = 0

        for post in BlogPost.objects.all():
            if post.post_picture:
                image_type = imghdr.what(None, h=bytes(post.post_picture))
                if not image_type:
                    self.stdout.write(self.style.WARNING(
                        f"Could not detect image type for Post {post.id}"
                    ))
                    continue

                filename = f"{uuid.uuid4().hex}.{image_type}"
                post.post_image.save(filename, ContentFile(post.post_picture))
                post.save()
                updated += 1
                self.stdout.write(f"Migrated image for Post {post.id} → {filename}")

        self.stdout.write(self.style.SUCCESS(f"Done! {updated} posts updated."))
