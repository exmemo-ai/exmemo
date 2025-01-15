from rest_framework import serializers
from .models import StoreEntry

class ListSerializer(serializers.ModelSerializer):
    updated_time = serializers.DateTimeField(format="%Y-%m-%d")
    created_time = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = StoreEntry
        fields = [
            "idx",
            "user_id",
            "block_id",
            "raw",
            "title",
            "ctype",
            "atype",
            "etype",
            "status",
            "addr",
            "path",
            "updated_time",
            "created_time",
        ]

    #def get_type(self, obj):
    #    return obj.get_type_display()

class DetailSerializer(serializers.ModelSerializer):
    updated_time = serializers.DateTimeField(format="%Y-%m-%d")
    created_time = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = StoreEntry
        fields = '__all__'

    #def get_type(self, obj):
    #    return obj.get_type_display()