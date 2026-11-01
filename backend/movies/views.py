from pathlib import Path
from uuid import uuid4
from django.conf import settings
from django.db import connection, transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from .export import export_movies
from .filters import filtered_movies
from .models import Favorite, Movie, MovieFile, Review, Watched
from .permissions import MoviePermission
from .serializers import MovieFileSerializer, MovieSerializer, ReviewSerializer
from .uploads import PosterParser, validate_poster


class MovieListCreateView(generics.ListCreateAPIView):
    serializer_class = MovieSerializer
    permission_classes = [MoviePermission]

    def get_queryset(self):
        return filtered_movies(self.request)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class MovieDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MovieSerializer
    permission_classes = [MoviePermission]

    def get_queryset(self):
        # Фильтры списка не должны случайно закрывать доступ к карточке.
        from django.db.models import Avg, Count, Exists, OuterRef
        queryset = Movie.objects.select_related("poster").annotate(
            average_rating=Avg("reviews__rating"), reviews_count=Count("reviews", distinct=True),
        )
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorite=Exists(Favorite.objects.filter(movie_id=OuterRef("pk"), owner=self.request.user)),
                is_watched=Exists(Watched.objects.filter(movie_id=OuterRef("pk"), owner=self.request.user)),
            )
        return queryset


class MovieExportView(APIView):
    def get(self, request):
        queryset = filtered_movies(request)
        if not request.user.is_staff:
            queryset = queryset.filter(is_favorite=True)
        return export_movies(queryset)


class PosterUploadView(APIView):
    parser_classes = [PosterParser]

    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        if not request.user.is_staff or movie.owner_id != request.user.id:
            raise PermissionDenied("Постер может менять только администратор, добавивший фильм.")
        upload = request.data.get("file")
        if upload is None or not hasattr(upload, "size"):
            raise ValidationError({"file": "Выберите файл постера."})
        suffix, mime = validate_poster(upload)
        name = f"{uuid4()}{suffix}"
        directory = Path(settings.MEDIA_ROOT) / "public"
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / name
        try:
            with transaction.atomic():
                # Два одновременных запроса не оставят два постера у одного фильма.
                Movie.objects.select_for_update().get(pk=pk)
                MovieFile.objects.filter(movie=movie).delete()
                with target.open("xb") as output:
                    for chunk in upload.chunks():
                        output.write(chunk)
                poster = MovieFile.objects.create(movie=movie, original_name=upload.name, stored_name=name,
                                                   mime=mime, size_bytes=upload.size)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return Response(MovieFileSerializer(poster).data, status=201)


class PosterDeleteView(APIView):
    def delete(self, request, pk):
        poster = get_object_or_404(MovieFile.objects.select_related("movie"), pk=pk)
        if not request.user.is_staff or poster.movie.owner_id != request.user.id:
            raise PermissionDenied("Нельзя удалить постер чужого фильма.")
        poster.delete()
        return Response(status=204)


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        get_object_or_404(Movie, pk=self.kwargs["pk"])
        return Review.objects.filter(movie_id=self.kwargs["pk"]).select_related("owner")

    def perform_create(self, serializer):
        with transaction.atomic():
            movie = get_object_or_404(Movie.objects.select_for_update(), pk=self.kwargs["pk"])
            if not Watched.objects.filter(movie=movie, owner=self.request.user).exists():
                raise ValidationError({"non_field_errors": "Сначала отметьте фильм как просмотренный."})
            if Review.objects.filter(movie=movie, owner=self.request.user).exists():
                raise ValidationError({"non_field_errors": "Вы уже оставили отзыв на этот фильм. Можно изменить его."})
            serializer.save(movie=movie, owner=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(owner=self.request.user).select_related("owner")

    def perform_update(self, serializer):
        if not Watched.objects.filter(movie=serializer.instance.movie, owner=self.request.user).exists():
            raise ValidationError({"non_field_errors": "Сначала отметьте фильм как просмотренный."})
        serializer.save()


class MyReviewView(APIView):
    def get(self, request, pk):
        get_object_or_404(Movie, pk=pk)
        review = Review.objects.filter(movie_id=pk, owner=request.user).select_related("owner").first()
        if review is None:
            return Response(status=204)
        return Response(ReviewSerializer(review).data)


class FavoriteView(APIView):
    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        favorite, created = Favorite.objects.get_or_create(movie=movie, owner=request.user)
        return Response({"id": favorite.id, "movie_id": movie.id}, status=201 if created else 200)

    def delete(self, request, pk):
        get_object_or_404(Movie, pk=pk)
        Favorite.objects.filter(movie_id=pk, owner=request.user).delete()
        return Response(status=204)


class WatchedView(APIView):
    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        watched, created = Watched.objects.get_or_create(movie=movie, owner=request.user)
        return Response({"movie_id": movie.id, "is_watched": True}, status=201 if created else 200)

    def delete(self, request, pk):
        with transaction.atomic():
            movie = get_object_or_404(Movie.objects.select_for_update(), pk=pk)
            if Review.objects.filter(movie=movie, owner=request.user).exists():
                raise ValidationError({"non_field_errors": "Чтобы снять отметку просмотра, сначала удалите свой отзыв."})
            Watched.objects.filter(movie=movie, owner=request.user).delete()
        return Response(status=204)


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            return Response({"status": "error", "database": "unavailable"}, status=503)
        return Response({"status": "ok", "database": "ok"})
