import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework_simplejwt.authentication import JWTAuthentication
from knox.views import LoginView as KnoxLoginView
from rest_framework import permissions, status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from silk.profiling.profiler import silk_profile
from .serializers import (BlogPostSerializer, PostCommentSerializer,
                          UserSerializer)
from .events import SubscribeNotificationProducer
from django.contrib.auth import get_user_model
from django.db.models import F, Prefetch
from .models import BlogPost, PostComment
from dotenv import load_dotenv
import base64
from django.db import transaction

load_dotenv()
User = get_user_model()

logger = logging.getLogger("webapp")


class BlogPostPagination(CursorPagination):
    ordering = '-last_modified'

class AuthorPagination(CursorPagination):
    ordering = 'date_joined'


class LoginView(KnoxLoginView):
    authentication_classes = [BasicAuthentication]


class IsAuthor(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    pagination_class = AuthorPagination

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, pk):
        user = self.get_object()
        email = request.data.get("email")
        if not email:
            return Response("email is required", status=status.HTTP_400_BAD_REQUEST)
        subscribed = True

        subscribe_producer = SubscribeNotificationProducer()

        if str.lower(self.request.method) == "post":
            subscribe_producer.send_event(user, email)
        if str.lower(self.request.method) == "delete":
            subscribe_producer.send_event(user, email, False)
            subscribed = False

        return Response(
            f"Successfully {'subscribed to' if subscribed else 'unsubscribed from'} notifications"
        )


class BlogPostViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    serializer_class = BlogPostSerializer
    queryset = BlogPost.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsAuthor]
    pagination_class = BlogPostPagination


    def get_permissions(self):
        if self.action in ("list", "retrieve", "picture"):
            return []
        elif self.action == 'like':
            return [permissions.IsAuthenticated()]

        return [permissions.IsAuthenticated(), IsAuthor()]

    @method_decorator(cache_page(60 * 15, key_prefix='blogpost'))
    @method_decorator(vary_on_headers("Authorization"))
    @silk_profile(name="blog_post_list")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        author_id = self.request.query_params.get("author_id")
        queryset = BlogPost.objects

        if author_id:
            queryset = queryset.filter(author__id=author_id)

        return queryset.prefetch_related(
            Prefetch(
                "postcomment_set", queryset=PostComment.objects.select_related("author")
            ),
            'likes'
        ).all()


    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        with transaction.atomic():
            post = self.get_object()
            user = request.user

            if post.likes.filter(id=user.id).exists():
                post.likes.remove(user)
                BlogPost.objects.filter(pk=post.pk).update(like_count=F('like_count') - 1)
                liked = False
            else:
                post.likes.add(user)
                BlogPost.objects.filter(pk=post.pk).update(like_count=F('like_count') + 1)
                liked = True

        post.refresh_from_db(fields=['like_count'])
        return Response({
            'liked': liked,
            'like_count': post.like_count,
        }, status=status.HTTP_200_OK)


class PostCommentViewSet(viewsets.ModelViewSet):
    queryset = PostComment.objects.all()
    serializer_class = PostCommentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
