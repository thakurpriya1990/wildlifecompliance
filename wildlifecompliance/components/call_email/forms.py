from django import forms
from django.core.exceptions import ValidationError
from ledger.accounts.models import EmailUser
from wildlifecompliance.components.call_email.models import (
        CallType,
        WildcareSpeciesType,
        WildcareSpeciesSubType,
        )
#from ckeditor.widgets import CKEditorWidget
from django.conf import settings
import pytz
from datetime import datetime, timedelta
#from . import errors


class WildcareSpeciesTypeAdminForm(forms.ModelForm):
    class Meta:
        model = WildcareSpeciesType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(WildcareSpeciesTypeAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['call_type'].queryset = CallType.objects.exclude(name__in=["general_enquiry", "illegal_activity"])

