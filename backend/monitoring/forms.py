from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import HelmetDevice


class WorkerUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False, help_text='Optional email address')
    worker_name = forms.CharField(max_length=100, label='Worker name')
    employee_id = forms.CharField(max_length=50, label='Employee ID')
    department = forms.CharField(max_length=100, label='Department')
    helmet = forms.ModelChoiceField(
        queryset=HelmetDevice.objects.filter(worker__isnull=True),
        required=False,
        empty_label='Select helmet to assign (optional)',
        label='Assign helmet'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'worker_name', 'employee_id', 'department', 'helmet')
