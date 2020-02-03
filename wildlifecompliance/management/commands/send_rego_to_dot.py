import datetime

from django.db import transaction

from django.core.management.base import BaseCommand
from django.db.models import Q, Max
from django.utils import timezone

import logging

from ledger.payments.invoice.models import Invoice

from wildlifecompliance import settings
from wildlifecompliance.components.sanction_outcome.email import send_remind_1st_period_overdue_mail, \
    email_detais_to_department_of_transport
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction, \
    AllegedCommittedOffence, DotRequestFile
from wildlifecompliance.components.sanction_outcome.serializers import SanctionOutcomeCommsLogEntrySerializer
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDate
from wildlifecompliance.components.sanction_outcome_due.serializers import SaveSanctionOutcomeDueDateSerializer
from wildlifecompliance.components.wc_payments.models import InfringementPenalty, InfringementPenaltyInvoice
from wildlifecompliance.helpers import DEBUG
from wildlifecompliance.management.commands.cron_tasks import get_infringement_notice_coordinators

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send the registration numbers the Department of Transport to get the details of the owners'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                logger.info('Running command {}'.format(__name__))
                today = timezone.localtime(timezone.now()).date()

                # Retrieve quersyset of SanctionOutcomes
                # type == 'infringement_notice'
                # is_parking_offence == True
                # status == 'with_dot'
                # details not sent to the DoT yet
                acos = AllegedCommittedOffence.objects.filter(Q(sanction_outcome__type=SanctionOutcome.TYPE_INFRINGEMENT_NOTICE) &
                                                              Q(sanction_outcome__status=SanctionOutcome.STATUS_WITH_DOT) &
                                                              Q(sanction_outcome__offender=None) &
                                                              Q(sanction_outcome__dot_request_files=None) &
                                                              Q(included=True) &
                                                              Q(alleged_offence__removed=False) &
                                                              Q(alleged_offence__section_regulation__is_parking_offence=True)).\
                                                        exclude(sanction_outcome__in=SanctionOutcome.objects.filter(
                                                            # Q(infringement_penalties__in=InfringementPenalty.objects.filter(
                                                            #     Q(invoice__payment_status=SanctionOutcome.PAYMENT_STATUS_PAID) &
                                                            #     Q(invoice__voided=False)
                                                            # ))
                                                            Q(infringement_penalty__in=InfringementPenalty.objects.filter(
                                                                Q(infringement_penalty_invoices__in=InfringementPenaltyInvoice.objects.filter(
                                                                    Q(invoice_reverence__in=Invoice.objects.filter(
                                                                        (Q(payment_status=SanctionOutcome.PAYMENT_STATUS_PAID) & Q(voided=False) | Q(voided=True))
                                                                    ).values('reference'))
                                                                ))
                                                            ))
                                                        ))
                                                        # exclude(sanction_outcome__payment_status=SanctionOutcome.PAYMENT_STATUS_PAID)

                count = acos.count()
                logger.info('{} parking infringement notice(s) found to process.'.format(str(count)))

                if count:
                    file_for_dot = DotRequestFile()
                    file_for_dot.save()  # Create the object to save manytomany fields

                    index = 1
                    for aco in acos:
                        file_for_dot.contents += aco.sanction_outcome.registration_number + ',' + str(index).zfill(2) + ',' + aco.sanction_outcome.offence_occurrence_date.strftime("%d%m%Y") + '\r\n'
                        file_for_dot.sanction_outcomes.add(aco.sanction_outcome)
                    file_for_dot.filename = 'DPaw-' + datetime.date.today().strftime("%d%b%Y") + '-Request.txt'
                    file_for_dot.save()

                    # Determine the bcc
                    members = get_infringement_notice_coordinators()
                    cc_list = [member.email for member in members] if members else [settings.NOTIFICATION_EMAIL]

                    # Email
                    to_address = ['shibaken+dot@dbca.gov.wa.au', ]
                    cc = cc_list
                    bcc = None
                    attachments = [(file_for_dot.filename, file_for_dot.contents, 'text/plain'), ]
                    email_data = email_detais_to_department_of_transport(to_address, attachments, cc, bcc)

                    # # Add communication log
                    if email_data:
                        for so in file_for_dot.sanction_outcomes.all():
                            email_data['sanction_outcome'] = so.id
                            serializer = SanctionOutcomeCommsLogEntrySerializer(data=email_data, partial=True)
                            serializer.is_valid(raise_exception=True)
                            serializer.save()

                    # Record action log per infringement notice
                    for so in file_for_dot.sanction_outcomes.all():
                        so.log_user_action(SanctionOutcomeUserAction.ACTION_SEND_TO_DOT.format(so.lodgement_number))
                        so.status = SanctionOutcome.STATUS_WITH_DOT  # probably already WITH_DOT
                        so.save()

                logger.info('Command {} completed'.format(__name__))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))
