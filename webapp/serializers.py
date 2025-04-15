from rest_framework import serializers
import logging

from .models import BlogPost, PostComment, User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

logger = logging.getLogger("webapp")


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
    author = UserSerializer(required=False, many=False, read_only=True)

    class Meta:
        model = PostComment
        fields = '__all__'
        extra_kwargs = {'author': {'read_only': True}}

    def validate(self, attrs):
        author = self.context['request'].user
        attrs['author'] = author

        return super().validate(attrs)



class BlogPostSerializer(serializers.ModelSerializer):
    comments = PostCommentSerializer(required=False, many=True, source="postcomment_set", read_only=True)
    author = UserSerializer(required=False, many=False, read_only=True)


    class Meta:
        model = BlogPost
        fields = ['id', 'author', 'title', 'text', 'comments', 'last_modified', 'post_image', 'likes']
        extra_kwargs = {'author': {'read_only': True}}

    def validate(self, attrs):
        author = self.context['request'].user
        attrs['author'] = author

        return super().validate(attrs)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token
