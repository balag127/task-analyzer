from rest_framework import serializers
from datetime import date


class TaskInputSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=255)
    due_date = serializers.DateField(required=False, allow_null=True)
    estimated_hours = serializers.FloatField(required=False)
    importance = serializers.IntegerField(required=False, min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )

    def validate(self, attrs):
        # Default values and extra validation
        if "importance" not in attrs or attrs["importance"] is None:
            attrs["importance"] = 5

        if "estimated_hours" not in attrs or attrs["estimated_hours"] is None:
            attrs["estimated_hours"] = 1.0

        if attrs["estimated_hours"] <= 0:
            attrs["estimated_hours"] = 1.0

        if "dependencies" not in attrs or attrs["dependencies"] is None:
            attrs["dependencies"] = []

        # Disallow due_date in the very far past (basic sanity check)
        due_date = attrs.get("due_date")
        if isinstance(due_date, date) and due_date.year < 1970:
            raise serializers.ValidationError("due_date looks invalid.")

        return attrs


class AnalyzeTasksRequestSerializer(serializers.Serializer):
    strategy = serializers.ChoiceField(
        choices=["fastest_wins", "high_impact", "deadline_driven", "smart_balance"],
        required=False,
        default="smart_balance",
    )
    tasks = TaskInputSerializer(many=True)


class ScoredTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    title = serializers.CharField()
    due_date = serializers.DateField(allow_null=True, required=False)
    estimated_hours = serializers.FloatField()
    importance = serializers.IntegerField()
    dependencies = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True
    )

    score = serializers.FloatField()
    priority_label = serializers.CharField()
    explanation = serializers.CharField()
    issues = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )


class AnalyzeTasksResponseSerializer(serializers.Serializer):
    strategy = serializers.CharField()
    tasks = ScoredTaskSerializer(many=True)


class SuggestTasksResponseSerializer(serializers.Serializer):
    strategy = serializers.CharField()
    suggested = ScoredTaskSerializer(many=True)
