# from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    AnalyzeTasksRequestSerializer,
    AnalyzeTasksResponseSerializer,
    SuggestTasksResponseSerializer,
)
from .scoring import score_tasks

# Simple in-memory cache of last analyzed tasks for /suggest.
_LAST_ANALYSIS_PAYLOAD = {
    "tasks": None,
    "strategy": "smart_balance",
}


class AnalyzeTasksView(APIView):
    """
    POST /api/tasks/analyze/

    Body:
    {
      "strategy": "smart_balance",
      "tasks": [ {...}, {...} ]
    }
    """

    def post(self, request, *args, **kwargs):
        serializer = AnalyzeTasksRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        strategy = serializer.validated_data["strategy"]
        tasks = serializer.validated_data["tasks"]

        scored = score_tasks(tasks, strategy=strategy)

        # Store for /suggest endpoint
        _LAST_ANALYSIS_PAYLOAD["tasks"] = tasks
        _LAST_ANALYSIS_PAYLOAD["strategy"] = strategy

        response_data = {
            "strategy": strategy,
            "tasks": scored,
        }
        out = AnalyzeTasksResponseSerializer(response_data)
        return Response(out.data, status=status.HTTP_200_OK)


class SuggestTasksView(APIView):
    """
    GET /api/tasks/suggest/

    Uses the last analyzed task list and returns top 3 'Smart Balance' tasks.
    If no previous analysis exists, returns a 400 error.
    """

    def get(self, request, *args, **kwargs):
        if not _LAST_ANALYSIS_PAYLOAD["tasks"]:
            return Response(
                {
                    "detail": "No analyzed tasks found. Call /api/tasks/analyze/ first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        tasks = _LAST_ANALYSIS_PAYLOAD["tasks"]
        # Always use smart_balance for suggestions
        strategy = "smart_balance"
        scored = score_tasks(tasks, strategy=strategy)
        suggested = scored[:3]

        response_data = {
            "strategy": strategy,
            "suggested": suggested,
        }
        out = SuggestTasksResponseSerializer(response_data)
        return Response(out.data, status=status.HTTP_200_OK)


