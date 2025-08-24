# documents/models.py
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('arrete', 'Arrêté'),
        ('certificat_medical', 'Certificat Médical'),
        ('contrat', 'Contrat'),
        ('autre', 'Autre'),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField(null=True, blank=True, default=1)
    content_object = GenericForeignKey('content_type', 'object_id')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    issuance_date = models.DateField(null=True, blank=True)
    issued_by = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    content_text = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='valide', choices=[('to_validate', 'À valider'), ('valide', 'Valide'), ('expiré', 'Expiré')])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} - {self.issued_by} ({self.issuance_date})"



