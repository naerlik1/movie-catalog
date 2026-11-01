from rest_framework import serializers
from .models import Movie, MovieFile, Review


class MovieFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MovieFile
        fields = ("id", "original_name", "stored_name", "mime", "size_bytes", "created_at", "url")

    def get_url(self, obj):
        return f"/media/{obj.stored_name}"


class MovieSerializer(serializers.ModelSerializer):
    owner_id = serializers.ReadOnlyField()
    poster = MovieFileSerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True, allow_null=True)
    reviews_count = serializers.IntegerField(read_only=True, default=0)
    is_favorite = serializers.BooleanField(read_only=True, default=False)
    is_watched = serializers.BooleanField(read_only=True, default=False)
    can_edit = serializers.SerializerMethodField()
    title = serializers.CharField(max_length=120, min_length=1, trim_whitespace=True,
                                  error_messages={"blank": "Введите название (до 120 символов)",
                                                  "max_length": "Введите название (до 120 символов)"})

    class Meta:
        model = Movie
        fields = ("id", "owner_id", "title", "year", "description", "poster", "average_rating",
                  "reviews_count", "is_favorite", "is_watched", "can_edit", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")

    def get_can_edit(self, obj):
        user = self.context["request"].user
        return user.is_authenticated and user.is_staff and obj.owner_id == user.id


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="owner.username")
    owner_id = serializers.ReadOnlyField()
    movie_id = serializers.ReadOnlyField()

    class Meta:
        model = Review
        fields = ("id", "movie_id", "owner_id", "username", "rating", "text", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")
