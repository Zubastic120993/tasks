from rest_framework import serializers
from .models import Category, Task
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class CategorySerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "owner", "created_at", "updated_at", "tasks_count"]

    def get_tasks_count(self, obj):
        return obj.task_set.count()


class TaskSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "completed",
            "priority",
            "category",
            "due_date",
            "owner",
            "created_at",
            "updated_at",
            "category_id",
        ]

        def create(self, validated_data):
            validated_data["owner"] = self.context["request"].user
            return super().create(validated_data)

        def update(self, instance, validated_data):
            validated_data["owner"] = self.context["request"].user
            return super().update(instance, validated_data)
