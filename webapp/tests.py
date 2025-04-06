from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import APITestCase, force_authenticate
from unittest.mock import patch


from webapp.models import BlogPost
from webapp.api_views import BlogPostViewSet

User = get_user_model()


class BlogPostTestCase(APITestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.username = "Тарас Шевченко"
        self.password = "Volya"
        self.user = User.objects.create_user(
            username=self.username, email="sheva@ua", password=self.password
        )
        self.post = BlogPost.objects.create(
            title="Мені 13й минало", text="Мені 13й минало", author=self.user
        )
        self.token_data = {
            'username': self.username,
            'password': self.password
        }

    @patch("pika.BlockingConnection", autospec=True)
    def test_blog_post_create_returns_201(self, pika_connection):
        request = self.factory.post(
            "/api/posts/",
            {"title": "Реве та стогне", "text": "Reve ta stogne Дніпр широкий"},
            content_type="application/json",
        )
        force_authenticate(request, self.user)
        view = BlogPostViewSet.as_view({"post": "create"})
        response = view(request)

        assert response.status_code == 201, "Status code must be 201."
        assert "id" in response.data, "Response must have id attribute"
        assert response.data["title"] == "Реве та стогне", "Wrong title of created post"

        pika_connection.assert_called_once()

    def test_blog_post_create_without_title_returns_400(self):
        request = self.factory.post(
            "/api/posts/",
            {"text": "Reve ta stogne dnipr shyrokiy"},
            content_type="application/json",
        )
        force_authenticate(request, self.user)
        view = BlogPostViewSet.as_view({"post": "create"})
        response = view(request)

        assert response.status_code == 400, "Status code must be 400"
        assert (
            "title" in response.data
        ), "Response error message must have title attribute"

    def test_create_post_unauthorized_returns_401(self):
        response = self.client.post(
            "/api/posts/",
            {"title": "Reve ta stogne", "text": "Reve ta stogne dnipr shyrokiy"},
        )

        assert response.status_code == 401, "Status code must be 401"

    def test_token_get_returns_200(self):
        response = self.client.post("/api/token/", data=self.token_data)

        assert response.status_code == 200, "Response code must be 200"
        assert "access" in response.data, "Token must be in response"

    def test_blog_post_obtain_returns_200(self):
        response = self.client.post("/api/token/", data=self.token_data)
        token = response.data["access"]

        test_post_id = self.post.id
        response = self.client.get(
            f"/api/posts/{test_post_id}/", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200, "Response status code must be 200"
        assert (
            "title" in response.data and response.data["title"] == "Мені 13й минало"
        ), "Title must be the same as in setUp"
