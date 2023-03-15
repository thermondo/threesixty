from django import forms

from . import models


class AnswerForm(forms.ModelForm):
    undo = forms.BooleanField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = models.Answer
        fields = ["decision", "question", "undo"]
        widgets = {"question": forms.HiddenInput}
