from rest_framework import serializers

from .models import BlogPost, PostComment, User
from .events import PostProducer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'id', 'groups', 'first_name']
        extra_kwargs = {'password': {'write_only': True}, 'id': {'read_only': True}}


    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'],
                                        validated_data.get('email'),
                                        validated_data['password'],
                                        first_name=validated_data.get('first_name'))
        groups = validated_data.get('groups')
        if groups:
            for group in groups:
                user.groups.add(group)
        return user


class PostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = '__all__'
        extra_kwargs = {'author': {'read_only': True}}

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)



class BlogPostSerializer(serializers.ModelSerializer):
    comments = PostCommentSerializer(required=False, many=True, source="postcomment_set", read_only=True)

    class Meta:
        model = BlogPost
        fields = ['id', 'author', 'title', 'text', 'comments', 'last_modified']
        extra_kwargs = {'author': {'read_only': True}}

    def create(self, validated_data):
        author = self.context['request'].user
        validated_data['author'] = author
        instance = super().create(validated_data)

        post_producer = PostProducer()
        post_producer.send_event(author, instance.pk)

        return instance