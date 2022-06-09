import pytz

from django import forms
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.conf import settings
from datetime import datetime, timedelta

from ledger.accounts.models import EmailUser
from wildlifecompliance.components.main.models import (
        SystemMaintenance, CallEmailTriageGroup, Region, District,
        VolunteerGroup, OfficerGroup, ManagerGroup,
        )


class SystemMaintenanceAdminForm(forms.ModelForm):
    class Meta:
        model = SystemMaintenance
        fields = '__all__'

    MSG = 'Start date cannot be before an existing records latest end_date. Start Date must be after'

    def clean(self):
        cleaned_data = self.cleaned_data
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        try:
            latest_obj = SystemMaintenance.objects.exclude(
                id=self.instance.id
            ).latest('start_date')

        except Exception:
            latest_obj = SystemMaintenance.objects.none()
        tz_local = pytz.timezone(settings.TIME_ZONE)  # start_date.tzinfo
        # tz_utc = pytz.timezone('utc')  # latest_obj.start_date.tzinfo

        if latest_obj:
            latest_end_date = latest_obj.end_date.astimezone(tz=tz_local)
            if self.instance.id:
                if start_date < latest_end_date and start_date \
                        < self.instance.start_date.astimezone(tz_local):

                    raise forms.ValidationError('{0} {1}'.format(
                        self.MSG,
                        latest_end_date.ctime()
                    ))
            else:
                if start_date < latest_end_date:
                    raise forms.ValidationError('{0} {1}'.format(
                        self.MSG,
                        latest_end_date.ctime()
                    ))

        if self.instance.id:
            if start_date < datetime.now(tz=tz_local) - timedelta(minutes=5) \
                    and start_date < self.instance.start_date.astimezone(tz_local):

                raise forms.ValidationError('Start date cannot be edited to be further in the past')
        else:
            if start_date < datetime.now(tz=tz_local) - timedelta(minutes=5):
                raise forms.ValidationError('Start date cannot be in the past')

        if end_date < start_date:
            raise forms.ValidationError('End date cannot be before start date')

        super(SystemMaintenanceAdminForm, self).clean()

        return cleaned_data


class GroupAdminFormTemplate(forms.ModelForm):
    #region = forms.ModelChoiceField(widget=RelatedFieldWidgetWrapper(can_add_related=False))
    #district = forms.ModelChoiceField(queryset=District.objects.filter(region=region), required=False)

    class Meta:
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            #import ipdb; ipdb.set_trace()
            #print(self.fields['region'].widget.__dict__)
            #print(self.fields['region']['widget'].__dict__)
            self.fields['members'].queryset = EmailUser.objects.filter(is_staff=True)
            self.fields['members'].required = False
            self.fields['region'].widget.can_add_related=False
            self.fields['region'].widget.can_change_related=False
            self.fields['region'].widget.can_delete_related=False
            self.fields['district'].widget.can_add_related=False
            self.fields['district'].widget.can_change_related=False
            self.fields['district'].widget.can_delete_related=False
            self.fields['district'].required=False

    def clean(self):
        print(self.Meta)
        print(self.Meta.__dict__)
        super().clean()
        if self.instance and self.Meta.model.objects.all().exists():
            try:
                original_members = self.Meta.model.objects.get(id=self.instance.id).members.all()
                current_members = self.cleaned_data.get('members')
                for o in original_members:
                    if o not in current_members:
                        if self.instance.member_is_assigned(o):
                            raise ValidationError('{} is currently assigned to a proposal(s)'.format(o.email))
            except:
                pass


class CallEmailTriageGroupAdminForm(GroupAdminFormTemplate):
    class Meta:
        model = CallEmailTriageGroup
        fields = '__all__'


class VolunteerGroupAdminForm(GroupAdminFormTemplate):
    class Meta:
        model = VolunteerGroup
        fields = '__all__'


class ManagerGroupAdminForm(GroupAdminFormTemplate):
    class Meta:
        model = ManagerGroup
        fields = '__all__'


class OfficerGroupAdminForm(GroupAdminFormTemplate):
    class Meta:
        model = OfficerGroup
        fields = '__all__'

