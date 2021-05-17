from django.contrib import admin, messages
from django.db import transaction
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.conf.urls import url

from wildlifecompliance.components.licences import models
from wildlifecompliance.components.licences import forms


@admin.register(models.LicenceCategory)
class LicenceCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.LicenceActivity)
class LicenceActivityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.WildlifeLicence)
class WildlifeLicence(admin.ModelAdmin):
    actions = [
        'verify_expired_licence',
        'verify_licence_renewal',
    ]

    def verify_expired_licence(self, request, queryset):
        from wildlifecompliance.components.licences.services import (
            LicenceService,
        )
        with transaction.atomic():

            for selected in queryset:
                LicenceService.verify_expired_licence_for(selected.id, request)

        self.message_user(
            request, 'Selected licence expired have been verified.')

    def verify_licence_renewal(self, request, queryset):
        from wildlifecompliance.components.licences.services import (
            LicenceService,
        )
        with transaction.atomic():

            for selected in queryset:
                LicenceService.verify_licence_renewal_for(selected.id, request)

        self.message_user(
            request, 'Selected licence renewals have been verified.')


class PurposeSpeciesInline(admin.TabularInline):
    '''
    HTML display with rich text for the Administration of Species Details to be
    added to the Wildlife Licence document.
    '''
    extra = 0
    model = models.PurposeSpecies
    exclude = ['header']


@admin.register(models.LicencePurpose)
class LicencePurposeAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'version', 'licence_purpose_actions'
    ]
    inlines = [
        PurposeSpeciesInline,
    ]
    actions = [
        'version_selected_Licence_purposes',
    ]

    ordering = ('name', '-version')
    list_filter = ('name',)
    readonly_fields = ('licence_purpose_actions',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r'^(?P<licence_purpose_id>.+)/process_generate_schema/$',
                self.admin_site.admin_view(self.process_generate_schema),
                name='generate-schema',
            ),
        ]
        return custom_urls + urls

    def version_selected_Licence_purposes(self, request, queryset):
        from wildlifecompliance.components.licences.services import (
            LicenceService,
        )
        warn = False
        with transaction.atomic():

            for selected in queryset:
                ok = LicenceService.version_licence_purpose(
                    selected.id, request
                )
                warn = warn if ok else True

        if warn:
            messages.warning(
                request, 'Not all Licence Purpose(s) have been versioned.')
        else:
            self.message_user(
                request, 'Selected Licence Purpose(s) have been versioned.')

    def licence_purpose_actions(self, obj):

        if obj.sections.count() > 0:

            return format_html(
                '<a class="button" href="{}">Generate Schema</a>&nbsp;',
                reverse('admin:generate-schema', args=[obj.pk]),
            )

        return ''
    licence_purpose_actions.short_description = 'Licence Purpose Actions'
    licence_purpose_actions.allow_tags = True

    def process_generate_schema(
        self, request, licence_purpose_id, *args, **kwargs
    ):
        return self.process_action(
            request=request,
            licence_purpose_id=licence_purpose_id,
            action_form=forms.GenerateSchemaForm,
            action_title='GenerateSchema',
        )

    def process_action(
        self,
        request,
        licence_purpose_id,
        action_form,
        action_title
    ):
        from wildlifecompliance.components.licences.services import (
            LicenceService,
        )
        licence_purpose = self.get_object(request, licence_purpose_id)

        schm = LicenceService.generate_licence_schema(licence_purpose, request)

        if request.method != 'POST':
            form = action_form()
        else:
            form = action_form(request.POST)
            if form.is_valid():
                try:
                    # form.save(proposal_type)
                    licence_purpose.schema = schm
                    licence_purpose.save()

                except Exception:
                    # If save() raised, the form will a have a non
                    # field error containing an informative message.
                    pass

                else:
                    self.message_user(request, 'Success')
                    url = reverse(
                        'admin:wildlifecompliance_licencepurpose_change',
                        args=[licence_purpose.pk],
                        current_app=self.admin_site.name,
                    )
                    return HttpResponseRedirect(url)

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['licence_purpose'] = licence_purpose
        context['title'] = action_title
        context['new_schema'] = schm

        return TemplateResponse(
            request,
            'wildlifecompliance/admin/licencepurpose_action.html',
            context,
        )


@admin.register(models.LicenceSpecies)
class LicenceSpeciesAdmin(admin.ModelAdmin):
    list_display = [
        'specie_id',
        'verify_date']
    readonly_fields = [
        'verify_date',
        'verify_id',
        'verify_token',
        'data']
    actions = ['verify_species']

    def verify_species(self, request, queryset):
        from wildlifecompliance.components.applications.services import (
            ApplicationService,
        )
        with transaction.atomic():

            for selected in queryset:
                ApplicationService.verify_licence_specie_id(selected.specie_id)

        self.message_user(request, 'Selected species have been verified.')


@admin.register(models.WildlifeLicenceReceptionEmail)
class WildlifeLicenceReceptionEmailAdmin(admin.ModelAdmin):
    pass


@admin.register(models.QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ['label', ]
    fields = ('label', )


@admin.register(models.QuestionOptionCondition)
class QuestionOptionConditionAdmin(admin.ModelAdmin):
    list_display = ['option', 'label']


@admin.register(models.MasterlistQuestion)
class MasterlistQuestionAdmin(admin.ModelAdmin):
    list_display = ['answer_type', 'question', ]
    filter_horizontal = ('option', )
    form = forms.MasterlistQuestionAdminForm


@admin.register(models.LicencePurposeSection)
class LicencePurposeSectionAdmin(admin.ModelAdmin):
    list_display = ['licence_purpose', 'index', 'section_label', ]
    fields = ('section_label', 'index', 'licence_purpose')


class SectionQuestionConditionInline(admin.TabularInline):
    extra = 0
    model = models.SectionQuestionCondition


@admin.register(models.SectionQuestion)
class SectionQuestionAdmin(admin.ModelAdmin):
    list_display = [
        'section',
        'section_question',
        'order',
        'section_parent_question',
        'parent_answer',
    ]
    inlines = [
        SectionQuestionConditionInline,
    ]
    form = forms.SectionQuestionAdminForm

    def section_question(self, obj):
        trim_text = obj.question.question
        return trim_text[:100] if trim_text else ''
    section_question.short_question = "question"

    def section_parent_question(self, obj):
        trim_text = obj.parent_question
        return trim_text.question[:100] if trim_text else ''
    section_parent_question.short_question = "question"

    def get_inline_instances(self, request, obj=None):
        inline = []

        if obj and obj.apply_special_conditions:

            if not obj.has_conditions:
                obj.set_conditions()

            inline = [
                inline(self.model, self.admin_site) for inline in self.inlines
            ]

        return inline
