from datetime import timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import load_workbook
from PIL import Image
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from .models import Favorite, Movie, MovieFile, Review, Watched

User = get_user_model()


class CatalogTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="admin", email="admin@test.example", password="TestPass123", is_staff=True)
        cls.other_admin = User.objects.create_user(username="otheradmin", email="otheradmin@test.example", password="TestPass123", is_staff=True)
        cls.alice = User.objects.create_user(username="alice", email="alice@test.example", password="TestPass123")
        cls.bob = User.objects.create_user(username="bob", email="bob@test.example", password="TestPass123")
        cls.movie = Movie.objects.create(owner=cls.admin, title="Первый фильм", year=2020, description="Описание")

    def setUp(self):
        cache.clear()
        self.temp = TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.temp.name)
        self.media_override.enable()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.media_override.disable)

    def auth(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def image(self, name="poster.png", content_type="image/png"):
        buffer = BytesIO()
        Image.new("RGB", (12, 16), "navy").save(buffer, format="PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)

    def test_register_case_insensitive_email_and_no_password_leak(self):
        body = {"username": "new_user", "email": "New@Test.Example", "password": "StudyPass123", "password_confirm": "StudyPass123"}
        response = self.client.post("/api/auth/register", body)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
        self.assertTrue(User.objects.get(username="new_user").check_password("StudyPass123"))
        body["username"] = "another_user"
        body["email"] = "new@test.example"
        response = self.client.post("/api/auth/register", body)
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data["errors"])

    def test_registration_field_errors(self):
        body = {"username": "я", "email": "bad", "password": "12345678", "password_confirm": "x"}
        response = self.client.post("/api/auth/register", body)
        self.assertEqual(response.status_code, 400)
        self.assertTrue({"username", "email", "password"} <= response.data["errors"].keys())
        body = {"username": "valid", "email": "valid@test.example", "password": "ValidPass123", "password_confirm": "different"}
        self.assertIn("password_confirm", self.client.post("/api/auth/register", body).data["errors"])

    def test_login_generic_error_and_ip_throttle(self):
        a = self.client.post("/api/auth/login", {"email": self.alice.email, "password": "wrong"})
        b = self.client.post("/api/auth/login", {"email": "missing@test.example", "password": "wrong"})
        self.assertEqual(a.data, b.data)
        for _ in range(8):
            self.assertEqual(self.client.post("/api/auth/login", {"email": "x", "password": "wrong"}).status_code, 400)
        self.assertEqual(self.client.post("/api/auth/login", {"email": self.alice.email, "password": "TestPass123"}).status_code, 429)
        self.assertEqual(self.client.post("/api/auth/login", {"email": self.alice.email, "password": "TestPass123"}, REMOTE_ADDR="192.0.2.5").status_code, 200)

    def test_jwt_24_hours_logout_and_expiration(self):
        response = self.client.post("/api/auth/login", {"email": self.alice.email.upper(), "password": "TestPass123"})
        token = AccessToken(response.data["access"])
        self.assertEqual(token["exp"] - token["iat"], 86400)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        expired = AccessToken.for_user(self.alice)
        expired.set_exp(from_time=timezone.now() - timedelta(days=2), lifetime=timedelta(hours=24))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {expired}")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_public_catalog_and_private_endpoints(self):
        self.assertEqual(self.client.get("/api/movies").status_code, 200)
        self.assertEqual(self.client.get(f"/api/movies/{self.movie.pk}").status_code, 200)
        for path in ("/api/auth/me", "/api/movies/export/", "/api/movies?scope=mine", "/api/movies?scope=favorites"):
            self.assertEqual(self.client.get(path).status_code, 401, path)
        self.assertEqual(self.client.post("/api/movies", {"title": "x", "year": 2020}).status_code, 401)

    def test_movie_crud_only_admin_owner(self):
        self.auth(self.alice)
        self.assertEqual(self.client.post("/api/movies", {"title": "x", "year": 2020}).status_code, 403)
        self.auth(self.admin)
        response = self.client.post("/api/movies", {"title": " Новый фильм ", "year": 2020, "description": "Текст"})
        self.assertEqual(response.status_code, 201)
        pk = response.data["id"]
        self.assertEqual(Movie.objects.get(pk=pk).title, "Новый фильм")
        self.auth(self.other_admin)
        self.assertEqual(self.client.patch(f"/api/movies/{pk}", {"title": "Чужой"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/movies/{pk}").status_code, 403)
        self.auth(self.admin)
        self.assertEqual(self.client.put(f"/api/movies/{pk}", {"title": "Изменён", "year": 2001, "description": "Новый текст"}).status_code, 200)
        self.assertEqual(self.client.delete(f"/api/movies/{pk}").status_code, 204)

    def test_movie_validation_and_mass_assignment(self):
        self.auth(self.admin)
        for body in ({"title": "   ", "year": 2020}, {"title": "x"*121, "year": 2020},
                     {"title": "x", "year": 1887}, {"title": "x", "year": "2020.5"},
                     {"title": "x", "year": 2020, "description": "x"*2001}):
            self.assertEqual(self.client.post("/api/movies", body).status_code, 400)
        result = self.client.post("/api/movies", {"title": "Safe", "year": 2020, "owner_id": self.bob.id})
        self.assertEqual(result.data["owner_id"], self.admin.pk)

    def test_review_unique_owner_isolation_and_rating_recalculation(self):
        self.auth(self.alice)
        Watched.objects.create(movie=self.movie, owner=self.alice)
        Watched.objects.create(movie=self.movie, owner=self.bob)
        path = f"/api/movies/{self.movie.pk}/reviews"
        result = self.client.post(path, {"rating": 8, "text": "Хорошо", "owner_id": self.bob.id})
        self.assertEqual(result.status_code, 201)
        pk = result.data["id"]
        self.assertEqual(result.data["owner_id"], self.alice.id)
        self.assertEqual(self.client.post(path, {"rating": 9, "text": "Ещё"}).status_code, 400)
        self.auth(self.bob)
        self.assertEqual(self.client.put(f"/api/reviews/{pk}", {"rating": 1, "text": "x"}).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/reviews/{pk}").status_code, 404)
        own_response = self.client.get(f"/api/movies/{self.movie.pk}/my-review")
        self.assertEqual(own_response.status_code, 204)
        self.assertEqual(own_response.content, b"")
        self.assertEqual(self.client.post(path, {"rating": 10, "text": "Отлично"}).status_code, 201)
        self.assertEqual(self.client.get(f"/api/movies/{self.movie.pk}").data["average_rating"], 9)
        self.auth(self.alice)
        self.client.put(f"/api/reviews/{pk}", {"rating": 6, "text": "Изменённый отзыв"})
        self.assertEqual(self.client.get(f"/api/movies/{self.movie.pk}").data["average_rating"], 8)
        self.client.delete(f"/api/reviews/{pk}")
        self.assertEqual(self.client.get(f"/api/movies/{self.movie.pk}").data["average_rating"], 10)

    def test_review_database_constraint_and_validation(self):
        self.auth(self.alice)
        Watched.objects.create(movie=self.movie, owner=self.alice)
        path = f"/api/movies/{self.movie.pk}/reviews"
        for rating in (0, 11, 5.5, "hello"):
            self.assertEqual(self.client.post(path, {"rating": rating, "text": "x"}).status_code, 400)
        self.assertEqual(self.client.post(path, {"rating": 5, "text": " "}).status_code, 400)
        Review.objects.create(movie=self.movie, owner=self.alice, rating=5, text="x")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Review.objects.create(movie=self.movie, owner=self.alice, rating=6, text="x")

    def test_review_requires_watched_and_mark_cannot_be_removed_with_review(self):
        path = f"/api/movies/{self.movie.pk}"
        self.auth(self.alice)
        Watched.objects.create(movie=self.movie, owner=self.bob)
        body = {"rating": 8, "text": "Хороший фильм", "is_watched": True, "owner_id": self.bob.id}
        response = self.client.post(f"{path}/reviews", body)
        self.assertEqual(response.status_code, 400)
        self.assertIn("просмотренный", response.data["errors"]["non_field_errors"])
        self.assertEqual(Review.objects.count(), 0)
        self.assertEqual(self.client.post(f"{path}/watched", {"owner_id": self.bob.id}).status_code, 201)
        self.assertEqual(self.client.post(f"{path}/watched").status_code, 200)
        self.assertEqual(Watched.objects.filter(owner=self.alice).count(), 1)
        response = self.client.post(f"{path}/reviews", body)
        self.assertEqual(response.status_code, 201)
        review_id = response.data["id"]
        self.assertEqual(response.data["owner_id"], self.alice.id)
        self.assertEqual(self.client.delete(f"{path}/watched").status_code, 400)
        self.assertTrue(self.client.get(path).data["is_watched"])
        self.assertEqual(self.client.delete(f"/api/reviews/{review_id}").status_code, 204)
        self.assertEqual(self.client.delete(f"{path}/watched").status_code, 204)
        self.assertFalse(self.client.get(path).data["is_watched"])
        self.assertEqual(self.client.post(f"{path}/reviews", body).status_code, 400)

    def test_watched_is_private_and_unique(self):
        path = f"/api/movies/{self.movie.pk}"
        self.assertEqual(self.client.post(f"{path}/watched").status_code, 401)
        self.assertEqual(self.client.delete(f"{path}/watched").status_code, 401)
        self.auth(self.alice)
        self.client.post(f"{path}/watched")
        self.assertTrue(self.client.get(path).data["is_watched"])
        self.assertTrue(self.client.get("/api/movies").data["results"][0]["is_watched"])
        with self.assertRaises(IntegrityError), transaction.atomic():
            Watched.objects.create(movie=self.movie, owner=self.alice)
        self.auth(self.bob)
        self.assertFalse(self.client.get(path).data["is_watched"])
        self.assertFalse(self.client.get("/api/movies").data["results"][0]["is_watched"])
        self.client.delete(f"{path}/watched")
        self.assertTrue(Watched.objects.filter(owner=self.alice).exists())
        self.assertEqual(self.client.post("/api/movies/999999/watched").status_code, 404)
        self.client.credentials()
        self.assertFalse(self.client.get(path).data["is_watched"])

    def test_review_update_also_requires_watched(self):
        review = Review.objects.create(movie=self.movie, owner=self.alice, rating=7, text="Отзыв")
        self.auth(self.alice)
        path = f"/api/reviews/{review.pk}"
        self.assertEqual(self.client.patch(path, {"rating": 9}).status_code, 400)
        self.client.post(f"/api/movies/{self.movie.pk}/watched")
        self.assertEqual(self.client.patch(path, {"rating": 9}).status_code, 200)
        self.assertEqual(self.client.get(f"/api/movies/{self.movie.pk}").data["average_rating"], 9)

    def test_favorites_unique_private_and_removed(self):
        path = f"/api/movies/{self.movie.pk}/favorite"
        self.auth(self.alice)
        self.assertEqual(self.client.post(path).status_code, 201)
        self.assertEqual(self.client.post(path).status_code, 200)
        self.assertEqual(Favorite.objects.count(), 1)
        self.assertEqual(self.client.get("/api/movies?scope=favorites").data["count"], 1)
        self.auth(self.bob)
        self.assertEqual(self.client.get("/api/movies?scope=favorites").data["count"], 0)
        self.client.delete(path)
        self.assertEqual(Favorite.objects.count(), 1)
        self.auth(self.alice)
        self.client.delete(path)
        self.assertEqual(Favorite.objects.count(), 0)

    def test_search_filters_pagination_and_invalid_filters(self):
        Movie.objects.create(owner=self.other_admin, title="Второй", year=2021, description="Космос")
        Review.objects.create(movie=self.movie, owner=self.alice, rating=8, text="x")
        self.assertEqual(self.client.get("/api/movies?search=космос").data["count"], 1)
        result = self.client.get("/api/movies?year=2020&rating_min=7&limit=1")
        self.assertEqual(result.data["count"], 1)
        self.assertEqual(result.data["results"][0]["id"], self.movie.id)
        self.assertIsNotNone(self.client.get("/api/movies?limit=1").data["next"])
        for query in ("year=x", "rating_min=11", "scope=bad", "ordering=bad"):
            self.assertEqual(self.client.get(f"/api/movies?{query}").status_code, 400)
        self.auth(self.admin)
        self.assertEqual(self.client.get("/api/movies?scope=mine").data["count"], 1)

    def test_poster_upload_replace_delete_and_cascade_on_disk(self):
        self.auth(self.admin)
        path = f"/api/movies/{self.movie.id}/files"
        result = self.client.post(path, {"file": self.image()}, format="multipart")
        self.assertEqual(result.status_code, 201)
        poster_path = Path(self.temp.name) / "public" / result.data["stored_name"]
        self.assertTrue(poster_path.exists())
        self.assertNotEqual(result.data["stored_name"], result.data["original_name"])
        with self.captureOnCommitCallbacks(execute=True):
            new = self.client.post(path, {"file": self.image()}, format="multipart")
        self.assertFalse(poster_path.exists())
        self.assertEqual(MovieFile.objects.count(), 1)
        poster_path = Path(self.temp.name) / "public" / new.data["stored_name"]
        self.auth(self.other_admin)
        self.assertEqual(self.client.delete(f"/api/files/{new.data['id']}").status_code, 403)
        self.auth(self.admin)
        Review.objects.create(movie=self.movie, owner=self.alice, rating=7, text="x")
        Favorite.objects.create(movie=self.movie, owner=self.alice)
        Watched.objects.create(movie=self.movie, owner=self.alice)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.client.delete(f"/api/movies/{self.movie.id}").status_code, 204)
        self.assertFalse(poster_path.exists())
        self.assertEqual(MovieFile.objects.count(), 0)
        self.assertEqual(Review.objects.count(), 0)
        self.assertEqual(Favorite.objects.count(), 0)
        self.assertEqual(Watched.objects.count(), 0)

    def test_poster_validation_type_size_mime_path_and_permissions(self):
        path = f"/api/movies/{self.movie.id}/files"
        self.auth(self.alice)
        self.assertEqual(self.client.post(path, {"file": self.image()}, format="multipart").status_code, 403)
        self.auth(self.admin)
        invalid = [SimpleUploadedFile("test.txt", b"text", content_type="text/plain"),
                   self.image("fake.jpg", "image/jpeg"), self.image("poster.png", "image/jpeg"),
                   SimpleUploadedFile("poster.png", b"not an image", content_type="image/png")]
        for file in invalid:
            self.assertEqual(self.client.post(path, {"file": file}, format="multipart").status_code, 415)
        huge = SimpleUploadedFile("huge.png", b"x"*(5*1024*1024+1), content_type="image/png")
        self.assertEqual(self.client.post(path, {"file": huge}, format="multipart").status_code, 413)
        for filename in (b'filename="../x.png"', b'filename=../x.png', b"filename*=utf-8''..%2Fx.png"):
            body = b'--test\r\nContent-Disposition: form-data; name="file"; ' + filename + b'\r\nContent-Type: image/png\r\n\r\n' + self.image().read() + b'\r\n--test--\r\n'
            self.assertEqual(self.client.post(path, body, content_type="multipart/form-data; boundary=test").status_code, 400)
        self.assertEqual(MovieFile.objects.count(), 0)

    def test_export_structure_filters_types_and_formula_safety(self):
        self.auth(self.admin)
        dangerous = Movie.objects.create(owner=self.admin, title="=1+1", year=2020, description="@SUM(A1:A2)")
        Review.objects.create(movie=dangerous, owner=self.alice, rating=9, text="x")
        response = self.client.get("/api/movies/export/?year=2020&search=%3D1%2B1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml.sheet", response["Content-Type"])
        workbook = load_workbook(BytesIO(response.content))
        sheet = workbook["Данные"]
        self.assertEqual(sheet.max_row, 2)
        self.assertEqual(sheet["B2"].value, "'=1+1")
        self.assertEqual(sheet["D2"].value, "'@SUM(A1:A2)")
        self.assertEqual(sheet["C2"].data_type, "n")
        self.assertEqual(sheet["F2"].data_type, "n")
        self.assertTrue(sheet["H2"].is_date)
        self.assertTrue(sheet["A1"].font.bold)
        self.assertEqual(sheet.freeze_panes, "A2")
        self.assertIsNotNone(sheet.auto_filter.ref)

    def test_export_only_favorites_for_user_and_all_for_admin(self):
        # Даже собственный фильм без отметки избранного не входит в клиентскую выгрузку.
        own = Movie.objects.create(owner=self.alice, title="Моё", year=2000)
        other = Movie.objects.create(owner=self.other_admin, title="Чужое избранное", year=2001)
        Favorite.objects.create(owner=self.alice, movie=self.movie)
        Favorite.objects.create(owner=self.bob, movie=other)
        self.auth(self.alice)
        for query in ("", "?scope=all", "?scope=favorites"):
            response = self.client.get(f"/api/movies/export/{query}")
            self.assertEqual(response.status_code, 200)
            sheet = load_workbook(BytesIO(response.content)).active
            self.assertEqual(sheet.max_row, 2)
            self.assertEqual(sheet["A2"].value, self.movie.id)
        self.auth(self.admin)
        sheet = load_workbook(BytesIO(self.client.get("/api/movies/export/").content)).active
        self.assertEqual(sheet.max_row, 4)

    def test_favorites_export_uses_filters_and_exports_all_pages(self):
        self.movie.title = "Alpha"
        self.movie.save()
        second = Movie.objects.create(owner=self.other_admin, title="Bravo", year=2020)
        excluded = Movie.objects.create(owner=self.admin, title="Charlie", year=2020)
        for movie in (self.movie, second):
            Favorite.objects.create(owner=self.alice, movie=movie)
            Review.objects.create(owner=self.bob, movie=movie, rating=9, text="Текст")
        Favorite.objects.create(owner=self.bob, movie=excluded)
        self.auth(self.alice)
        query = "scope=favorites&search=a&year=2020&rating_min=8&ordering=title&limit=1&page=2"
        listing = self.client.get(f"/api/movies?{query}")
        self.assertEqual(listing.data["count"], 2)
        self.assertEqual(len(listing.data["results"]), 1)
        sheet = load_workbook(BytesIO(self.client.get(f"/api/movies/export/?{query}").content)).active
        self.assertEqual(sheet.max_row, 3)
        self.assertEqual([sheet.cell(row, 1).value for row in (2, 3)], [self.movie.id, second.id])
        sheet = load_workbook(BytesIO(self.client.get("/api/movies/export/?scope=favorites&search=Bravo").content)).active
        self.assertEqual(sheet.max_row, 2)
        self.assertEqual(sheet["A2"].value, second.id)

    def test_empty_favorites_export_has_headers(self):
        self.auth(self.bob)
        response = self.client.get("/api/movies/export/?scope=favorites")
        self.assertEqual(response.status_code, 200)
        sheet = load_workbook(BytesIO(response.content)).active
        self.assertEqual(sheet.max_row, 1)
        self.assertEqual(sheet["A1"].value, "ID")

    def test_export_limit_is_not_silent_truncation(self):
        self.auth(self.admin)
        with patch("django.db.models.query.QuerySet.count", return_value=10001):
            result = self.client.get("/api/movies/export/")
        self.assertEqual(result.status_code, 400)
        self.assertIn("10 000", result.data["errors"]["export"])

    def test_health_checks_database(self):
        self.assertEqual(self.client.get("/health").data["database"], "ok")
