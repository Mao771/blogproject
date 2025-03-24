from django.contrib import admin
from .models import BlogPost, PostComment

admin.site.register(BlogPost)
admin.site.register(PostComment)
