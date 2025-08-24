# audit/serializers.py
from rest_framework import serializers
from auditlog.models import LogEntry
from django.contrib.contenttypes.models import ContentType

class ContentTypeSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ["id", "app_label", "model"]

class LogEntrySerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    content_type = ContentTypeSlimSerializer(read_only=True)
    get_action_display = serializers.CharField(read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = "__all__"  # or list them explicitly
        read_only_fields = tuple(fields)

    def get_actor(self, obj):
        u = obj.actor
        return {"id": u.id, "username": u.username, "role": getattr(u, "role", None)} if u else None

    def get_url(self, obj):
        return getattr(obj, "url", None)
