from django import forms

from . import models


class AnswerForm(forms.ModelForm):

    def __init__(self, user=None, *args, **kwargs):
        super(AnswerForm, self).__init__(*args, **kwargs)
        self.fields["undo"] = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean_undo(self):
        undo = self.cleaned_data['undo']
        if undo != "false" and undo != "true":
            self.add_error('undo', 'must be true or false')

    class Meta:
        model = models.Answer
        fields = ['decision', 'question']
        widgets = {
            'question': forms.HiddenInput
        }
