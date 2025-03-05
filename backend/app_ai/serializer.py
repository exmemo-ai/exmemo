from rest_framework import serializers

from .models import StorePrompt


class StorePromptSerializer(serializers.ModelSerializer):
    created_time = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = StorePrompt
        fields = ["idx", "user_id", "title", "prompt", "etype", "created_time"]

    def get_type(self, obj):
        return obj.get_type_display()

