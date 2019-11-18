from django.db import models
from django.db.models import Q

from ledger.accounts.models import RevisionedMixin, EmailUser


class SanctionOutcomeDueDateConfiguration(RevisionedMixin):
    due_date_window_1st =  models.PositiveSmallIntegerField(blank=True, null=True, )  # unit: [days]
    due_date_window_2nd =  models.PositiveSmallIntegerField(blank=True, null=True, )  # unit: [days]
    date_of_enforcement = models.DateField(blank=True, null=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_SanctionOutcomeDueDateConfiguration'
        verbose_name_plural = 'CM_SanctionOutcomeDueDateConfiguration'
        ordering = ('date_of_enforcement', )  # oldest record first, latest record last

    @classmethod
    def get_config_by_date(cls, date_of_issue):
        return cls.objects.filter(Q(date_of_enforcement__lte=date_of_issue)).order_by('date_of_enforcement', ).last()

    def __str__(self):
        return '1st due date window: {} days, 2nd due date window: {} days, enforcement date: {})'.format(self.due_date_window_1st, self.due_date_window_2nd, self.date_of_enforcement)


class SanctionOutcomeDueDate(models.Model):
    due_date_1st = models.DateField(null=True, blank=True)
    due_date_2nd = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reason_for_extension = models.TextField(blank=True)
    extended_by = models.ForeignKey(EmailUser, null=True)
    sanction_outcome = models.ForeignKey('SanctionOutcome', null=False, related_name='due_dates')

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_SanctionOutcomeDueDate'
        verbose_name_plural = 'CM_SanctionOutcomeDueDates'
        ordering = ('created_at',)