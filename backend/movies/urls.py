from django.urls import path
from .views import (FavoriteView, MovieDetailView, MovieExportView, MovieListCreateView, MyReviewView,
                    PosterDeleteView, PosterUploadView, ReviewDetailView, ReviewListCreateView, WatchedView)

urlpatterns = [
    path("movies", MovieListCreateView.as_view()),
    path("movies/export/", MovieExportView.as_view()),
    path("movies/<int:pk>", MovieDetailView.as_view()),
    path("movies/<int:pk>/files", PosterUploadView.as_view()),
    path("files/<int:pk>", PosterDeleteView.as_view()),
    path("movies/<int:pk>/reviews", ReviewListCreateView.as_view()),
    path("movies/<int:pk>/my-review", MyReviewView.as_view()),
    path("reviews/<int:pk>", ReviewDetailView.as_view()),
    path("movies/<int:pk>/favorite", FavoriteView.as_view()),
    path("movies/<int:pk>/watched", WatchedView.as_view()),
]
