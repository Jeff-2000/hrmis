# feedback/serializers.py
from rest_framework import serializers
from .feedback_models import Feedback

class FeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ["rating","comment","page_url","user_agent"]

    def validate_rating(self, v):
        if v not in [1,2,3,4,5]:
            raise serializers.ValidationError("Rating must be 1..5")
        return v
