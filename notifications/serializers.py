# notifications/serializers.py

from rest_framework import serializers
from .models import Notification, NotificationPreference
from authentication.models import User

# class NotificationSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField(read_only=True)

#     class Meta:
#         model = Notification
#         fields = ['id', 'user', 'channel', 'recipient', 'message', 'status', 'timestamp']
#         read_only_fields = ['user', 'status', 'timestamp']

class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id','user','channel','recipient','title','message','category','priority',
            'status','is_read','read_at','delivered_at','timestamp','provider','provider_message_id','metadata'
        ]
        read_only_fields = ['user','status','read_at','delivered_at','timestamp','provider','provider_message_id','metadata']


from rest_framework import serializers
from django.db.models import Q
from .models import NotificationPreference

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = NotificationPreference
        fields = ['id', 'user', 'channel', 'contact', 'is_active', 'created_at']
        read_only_fields = ['user', 'created_at']

    def validate(self, data):
        request = self.context.get("request")
        user = request.user if request else None
        channel = data.get("channel")
        contact = data.get("contact")

        # Only check for duplicates when creating
        if self.instance is None and NotificationPreference.objects.filter(user=user, channel=channel).exists():
            raise serializers.ValidationError({
                "channel": "Une préférence existe déjà pour ce canal. Veuillez en modifier une existante ou utiliser un autre canal."
            })

        return data

        
        