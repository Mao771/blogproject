import base64

from decouple import config
from django.contrib.auth import authenticate, login
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.conf import settings


from .forms import BlogPostCommentForm, BlogPostCreateForm
from .models import BlogPost, PostComment


def jwks_view(request):
    return JsonResponse({
        "keys": [settings.SIMPLE_JWT['VERIFYING_KEY']]
    })


def index_view(request):
    if not request.user:
        user = authenticate(request, username=config("USER"), password=config("PASS"))
        login(request, user)

    all_posts = BlogPost.objects.all()

    for b_post in all_posts:
        b_post.base64_image = (
            base64.b64encode(b_post.post_picture).decode("utf-8")
            if b_post.post_picture is not None
            else None
        )

    return render(request, "blog.html", {"blog_posts": all_posts})


@login_required
def create_post(request):
    if request.method == "POST":
        form = BlogPostCreateForm(request.POST, request.FILES)
        if form.is_valid():
            b_post = BlogPost(
                title=request.POST["title"],
                text=request.POST["text"],
                author=request.user,
                post_picture=(
                    request.FILES["post_picture"].read()
                    if "post_picture" in request.FILES
                    else None
                ),
            )
            b_post.save()

            return HttpResponseRedirect(reverse("index"))
    else:
        form = BlogPostCreateForm()
    return render(
        request, "create_post.html", {"form": form, "title": "Створення нового допису"}
    )


def display_post(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    post.base64_image = (
        base64.b64encode(post.post_picture).decode("utf-8")
        if post.post_picture is not None
        else None
    )
    form = BlogPostCreateForm()
    if isinstance(post, BlogPost):
        comments = PostComment.objects.filter(post=post)
    else:
        comments = []

    return render(
        request, "read_post.html", {"post": post, "comments": comments, "form": form}
    )


@login_required
def comment_post(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    post.base64_image = (
        base64.b64encode(post.post_picture).decode("utf-8")
        if post.post_picture is not None
        else None
    )
    if isinstance(post, BlogPost):
        comments = PostComment.objects.filter(post=post)
    else:
        comments = []
    if request.method == "POST":
        form = BlogPostCommentForm(request.POST)
        if form.is_valid():
            b_comment = PostComment(
                post=post, text=request.POST["text"], author=request.user
            )
            b_comment.save()

    form = BlogPostCommentForm()

    return render(
        request, "read_post.html", {"post": post, "comments": comments, "form": form}
    )


@login_required
def like_post(request, post_id):
    BlogPost.objects.filter(pk=post_id).update(
        like_count=F("like_count") + 1
    )  # атомарна операція
    form = BlogPostCommentForm()
    post = get_object_or_404(BlogPost, pk=post_id)
    post.base64_image = (
        base64.b64encode(post.post_picture).decode("utf-8")
        if post.post_picture is not None
        else None
    )
    if isinstance(post, BlogPost):
        comments = PostComment.objects.filter(post=post)
    else:
        comments = []

    return render(
        request, "read_post.html", {"post": post, "comments": comments, "form": form}
    )
