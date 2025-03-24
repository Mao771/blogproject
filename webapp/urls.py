from django.urls import include, path
from rest_framework import routers
from knox import views as knox_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from . import api_views, views

router = routers.DefaultRouter()
router.register('authors', api_views.UserViewSet, basename='authors')
router.register('posts', api_views.BlogPostViewSet, basename='posts')
router.register('comments', api_views.PostCommentViewSet, basename='comments')


urlpatterns = [
    path("", views.index_view, name="index"),
    path("jwks", views.jwks_view, name="jwks"),
    path("create", views.create_post, name="create"),
    path("post/<int:post_id>/", views.display_post, name="display_post"),
    path('post/<int:post_id>/comment/', views.comment_post, name='comment_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),

    path("api/", include(router.urls), name="api"),

    path('api/login/', api_views.LoginView.as_view(), name='knox_login'),
    path('api/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('api/logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
