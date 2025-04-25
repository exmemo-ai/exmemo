from rest_framework import serializers

from .models import StoreEntry
from .entry_item import EntryItem


class StoreEntrySerializer(serializers.ModelSerializer):
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

    def get_type(self, obj):
        return obj.get_type_display()

    def to_representation(self, instance):
        entry_item = EntryItem.from_model(instance)
        return entry_item.to_dict()