from rest_framework import serializers

from .models import StoreEnglishArticle, StoreTranslate


class StoreTranslateSerializer(serializers.ModelSerializer):
    created_time = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = StoreTranslate
        fields = ["idx", "user_id", "word", "info", "freq", "times", "created_time"]

    def get_type(self, obj):
        return obj.get_type_display()


class StoreEnglishArticleSerializer(serializers.ModelSerializer):
    created_time = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = StoreEnglishArticle
        fields = ["idx", "user_id", "title", "content", "info", "created_time"]

    def get_type(self, obj):
        return obj.get_type_display()
