from django.db.models import Avg, BooleanField, Count, Exists, OuterRef, Q, Value
from rest_framework import serializers
from rest_framework.exceptions import NotAuthenticated
from .models import Favorite, Movie, Watched


class MovieFilterSerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True, max_length=120)
    year = serializers.IntegerField(required=False, min_value=1888, max_value=9999)
    rating_min = serializers.FloatField(required=False, min_value=0, max_value=10)
    scope = serializers.ChoiceField(choices=["all", "mine", "favorites"], default="all")
    ordering = serializers.ChoiceField(choices=["newest", "title", "year", "rating"], default="newest")


def filtered_movies(request):
    params = MovieFilterSerializer(data=request.query_params)
    params.is_valid(raise_exception=True)
    filters = params.validated_data
    user = request.user
    if filters["scope"] != "all" and not user.is_authenticated:
        raise NotAuthenticated()
    queryset = Movie.objects.select_related("poster").annotate(
        average_rating=Avg("reviews__rating"), reviews_count=Count("reviews", distinct=True),
    )
    if user.is_authenticated:
        queryset = queryset.annotate(
            is_favorite=Exists(Favorite.objects.filter(movie_id=OuterRef("pk"), owner=user)),
            is_watched=Exists(Watched.objects.filter(movie_id=OuterRef("pk"), owner=user)),
        )
    else:
        queryset = queryset.annotate(
            is_favorite=Value(False, output_field=BooleanField()),
            is_watched=Value(False, output_field=BooleanField()),
        )
    if filters["scope"] == "mine":
        queryset = queryset.filter(owner=user)
    elif filters["scope"] == "favorites":
        queryset = queryset.filter(is_favorite=True)
    if filters.get("search"):
        queryset = queryset.filter(Q(title__icontains=filters["search"]) | Q(description__icontains=filters["search"]))
    if filters.get("year"):
        queryset = queryset.filter(year=filters["year"])
    if "rating_min" in filters:
        queryset = queryset.filter(average_rating__gte=filters["rating_min"])
    orderings = {"newest": ("-created_at", "-id"), "title": ("title", "id"),
                 "year": ("-year", "id"), "rating": ("-average_rating", "id")}
    # NULL-рейтинги идут после оценённых фильмов, в PostgreSQL DESC по умолчанию наоборот.
    if filters["ordering"] == "rating":
        from django.db.models import F
        return queryset.order_by(F("average_rating").desc(nulls_last=True), "id")
    return queryset.order_by(*orderings[filters["ordering"]])
