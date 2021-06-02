from django import forms

from wildlifecompliance.components.licences.models import MasterlistQuestion
from wildlifecompliance.components.licences.models import QuestionOption
from wildlifecompliance.components.licences.models import SectionQuestion


class MasterlistQuestionAdminForm(forms.ModelForm):
    # help_text = forms.CharField(widget=CKEditorWidget())
    # help_text_assessor = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = MasterlistQuestion
        fields = (
            'question',
            'option',
            'answer_type',
            # 'help_text_url',
            # 'help_text_assessor_url',
            # 'help_text',
            # 'help_text_assessor'
        )

    def __init__(self, *args, **kwargs):
        super(MasterlistQuestionAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['option'].queryset = QuestionOption.objects.all()


class SectionQuestionAdminForm(forms.ModelForm):
    class Meta:
        model = SectionQuestion
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(SectionQuestionAdminForm, self).__init__(*args, **kwargs)


class LicencePurposeActionForm(forms.Form):
    new_schema = forms.CharField(
        required=False,
        widget=forms.Textarea,
    )

    def form_action(self, licence_purpose):
        raise NotImplementedError()

    def save(self, licence_purpose):
        try:
            licence_purpose, action = self.form_action(licence_purpose)

        except self.errors.Error as e:
            error_message = str(e)
            self.add_error(None, error_message)
            raise

        return licence_purpose, action


class GenerateSchemaForm(LicencePurposeActionForm):
    # comment = forms.CharField(
    #     required=False,
    #     widget=forms.Textarea,
    # )

    field_order = (
        'new_schema',
    )

    def form_action(self, licence_purpose):
        return licence_purpose
