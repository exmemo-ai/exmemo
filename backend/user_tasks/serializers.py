from rest_framework import serializers
from .models import UserTask

class UserTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTask
        fields = ['idx', 'user_id', 'task_id', 'task_name', 'status', 'created_time', 'updated_time', 'progress']
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data['user_id'] = self.context['request'].user_id
        return super().create(validated_data)
