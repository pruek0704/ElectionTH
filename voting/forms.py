# voting/forms.py

from django import forms
from .models import Citizen


class CitizenLoginForm(forms.Form):
    full_name = forms.CharField(
        label='ชื่อ-นามสกุล',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'กรอกชื่อ-นามสกุล',
            'autocomplete': 'off',
        })
    )
    national_id = forms.CharField(
        label='เลขบัตรประชาชน',
        max_length=13,
        min_length=13,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'กรอกเลขบัตรประชาชน 13 หลัก',
            'inputmode': 'numeric',
        })
    )

    def clean_national_id(self):
        nid = self.cleaned_data.get('national_id', '')
        if not nid.isdigit():
            raise forms.ValidationError('เลขบัตรประชาชนต้องเป็นตัวเลขเท่านั้น')
        if len(nid) != 13:
            raise forms.ValidationError('เลขบัตรประชาชนต้องมี 13 หลัก')
        return nid

    def authenticate(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        national_id = self.cleaned_data.get('national_id', '')
        try:
            citizen = Citizen.objects.get(
                full_name=full_name,
                national_id=national_id,
                is_active=True
            )
            return citizen
        except Citizen.DoesNotExist:
            return None