from django import forms

from . import models


class AnswerForm(forms.ModelForm):
    class Meta:
        model = models.Answer
        fields = ['decision', 'question']
        widgets = {
            'question': forms.HiddenInput
        }
