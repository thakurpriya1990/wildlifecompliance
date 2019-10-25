from django import forms
from django.contrib import admin
from reversion.admin import VersionAdmin

from wildlifecompliance.components.offence import models
from wildlifecompliance.components.offence.models import PenaltyAmount


class PenaltyAmountInline(admin.TabularInline):
    model = PenaltyAmount


@admin.register(models.Offence)
class OffenceAdmin(admin.ModelAdmin):
    filter_horizontal = ('alleged_offences',)


class SectionRegulationForm(forms.ModelForm):
    offence_text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = models.SectionRegulation
        fields = '__all__'


class SectionRegulationAdmin(VersionAdmin):
    form = SectionRegulationForm
    inlines = [PenaltyAmountInline,]


@admin.register(models.PenaltyAmount)
class PenaltyAmountAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.SectionRegulation, SectionRegulationAdmin)

