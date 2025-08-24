from django import forms
from .models import Situation

class SituationForm(forms.ModelForm):
    class Meta:
        model = Situation
        fields = [
            'situation_type', 'start_date', 'end_date', 'status', 'document',
            'tranche_1_start', 'tranche_1_end', 'tranche_2_start', 'tranche_2_end',
            'tranche_3_start', 'tranche_3_end', 'training_details', 'training_location',
            'physical_control', 'resumption_date', 'detachment_duration',
            'availability_reason', 'exclusion_reason', 'exit_type'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'tranche_1_start': forms.DateInput(attrs={'type': 'date'}),
            'tranche_1_end': forms.DateInput(attrs={'type': 'date'}),
            'tranche_2_start': forms.DateInput(attrs={'type': 'date'}),
            'tranche_2_end': forms.DateInput(attrs={'type': 'date'}),
            'tranche_3_start': forms.DateInput(attrs={'type': 'date'}),
            'tranche_3_end': forms.DateInput(attrs={'type': 'date'}),
            'resumption_date': forms.DateInput(attrs={'type': 'date'}),
            'status': forms.Select(),
            'situation_type': forms.Select(),
            'document': forms.Select(),
            'physical_control': forms.CheckboxInput(),
            'training_details': forms.TextInput(),
            'training_location': forms.TextInput(),
            'detachment_duration': forms.TextInput(),
            'availability_reason': forms.Textarea(attrs={'rows': 3}),
            'exclusion_reason': forms.Textarea(attrs={'rows': 3}),
            'exit_type': forms.TextInput()
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")
        return cleaned_data