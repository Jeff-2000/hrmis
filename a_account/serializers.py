# a_account/serializers.py
from rest_framework import serializers
from .models import UserSetting

class UserSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSetting
        fields = "__all__"
        read_only_fields = ["id","user","updated_at"]
