# recon/forms.py

from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'project_type', 'project_url', 'scopes', 'out_of_scope', 'source', 'source_other']
        widgets = {
            'scopes': forms.Textarea(attrs={'rows': 5}),
            'out_of_scope': forms.Textarea(attrs={'rows': 5}),
        }

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source')
        source_other = cleaned_data.get('source_other')

        if source == 'Other' and not source_other:
            self.add_error('source_other', 'Please specify the source.')
