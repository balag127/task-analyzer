import json
from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(null=True, blank=True)
    importance = models.PositiveIntegerField(default=5)

    # Use TextField instead of JSONField for SQLite
    dependencies_raw = models.TextField(default="[]", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def dependencies(self):
        """Return dependencies as Python list"""
        try:
            return json.loads(self.dependencies_raw)
        except:
            return []

    @dependencies.setter
    def dependencies(self, value):
        """Save list as JSON"""
        try:
            self.dependencies_raw = json.dumps(value)
        except:
            self.dependencies_raw = "[]"

    def __str__(self):
        return self.title
