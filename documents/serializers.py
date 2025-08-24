from rest_framework import serializers
from .models import Document
from rest_framework.serializers import ModelSerializer
# class DocumentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Document
#         fields = '__all__'

#     def validate(self, data):
#         if not data.get('file') and not data.get('content_text'):
#             raise serializers.ValidationError("Either a file or content_text must be provided.")
#         return data
    
    
    
from rest_framework import serializers
from .models import Document
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'

    def validate(self, data):
        # Require file or content_text
        if not data.get('file') and not data.get('content_text'):
            raise serializers.ValidationError("Either a file or content_text must be provided.")
        # Require document_type, issuance_date, and issued_by
        if not data.get('document_type'):
            raise serializers.ValidationError("Document type is required.")
        if not data.get('issuance_date'):
            raise serializers.ValidationError("Issuance date is required.")
        if not data.get('issued_by'):
            raise serializers.ValidationError("Issued by is required.")
        # Require content_type and object_id
        if not data.get('content_type'):
            raise serializers.ValidationError("Content type is required.")
        if data.get('object_id') is None:
            raise serializers.ValidationError("Object ID is required.")
        return data


class ContentTypeSerializer(ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']



