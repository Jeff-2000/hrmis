from django.core.management.base import BaseCommand
from leave.models import Holiday
from datetime import date

class Command(BaseCommand):
    help = 'Populate Côte d\'Ivoire public holidays for 2025'

    def handle(self, *args, **options):
        holidays_2025 = [
            (date(2025, 1, 1), "Nouvel An", "Côte d'Ivoire"),
            (date(2025, 4, 21), "Lundi de Pâques", "Côte d'Ivoire"),
            (date(2025, 5, 1), "Fête du Travail", "Côte d'Ivoire"),
            (date(2025, 5, 29), "Ascension", "Côte d'Ivoire"),
            (date(2025, 6, 9), "Lundi de Pentecôte", "Côte d'Ivoire"),
            (date(2025, 8, 7), "Fête de l'Indépendance", "Côte d'Ivoire"),
            (date(2025, 8, 15), "Assomption", "Côte d'Ivoire"),
            (date(2025, 11, 1), "Toussaint", "Côte d'Ivoire"),
            (date(2025, 11, 15), "Journée Nationale de la Paix", "Côte d'Ivoire"),
            (date(2025, 12, 25), "Noël", "Côte d'Ivoire"),
            # Add Islamic holidays (approximate, as they depend on lunar calendar)
            (date(2025, 3, 1), "Tabaski (approximatif)", "Côte d'Ivoire"),
            (date(2025, 2, 28), "Aïd el-Fitr (approximatif)", "Côte d'Ivoire"),
            (date(2025, 10, 27), "Maouloud (approximatif)", "Côte d'Ivoire"),
        ]

        for holiday_date, name, region in holidays_2025:
            Holiday.objects.get_or_create(
                date=holiday_date,
                defaults={'name': name, 'region': region}
            )
        self.stdout.write(self.style.SUCCESS('Successfully populated Côte d\'Ivoire holidays for 2025'))