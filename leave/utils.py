# leave/utils.py
from datetime import date
from .models import Holiday

def is_working_day(check_date):
    if check_date.weekday() >= 5:  # Saturday or Sunday
        return False
    if Holiday.objects.filter(date=check_date).exists():
        return False
    return True



# def is_working_day(check_date):
#     if check_date.weekday() >= 5:  # Saturday or Sunday
#         return False
#     if Holiday.objects.filter(date=check_date, region__in=['', 'Côte d'Ivoire']).exists():
#         return False
#     return True
    
    
    

