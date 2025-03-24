import datetime
from dataclasses import dataclass
from rest_framework import serializers

@dataclass
class BlogPost:
    title: str
    text: str
    like_count: int
    author: str
    created: datetime.datetime


blog_post = BlogPost(title='Test post',
                     text='This is post about something and other stuff.',
                     author="Jhon White",
                     like_count=10,
                     created=datetime.datetime.now())


class BlogPostSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    text = serializers.CharField(max_length=200)
    author = serializers.CharField(max_length=200)
    like_count = serializers.IntegerField()
    created = serializers.DateTimeField()

serializer = BlogPostSerializer(blog_post)
print(serializer.data)
