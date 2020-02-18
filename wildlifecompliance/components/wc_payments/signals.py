import logging
from django.db.models.signals import post_save
from ledger.payments.cash.models import CashTransaction
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction
from wildlifecompliance.components.wc_payments.models import InfringementPenaltyInvoice


logger = logging.getLogger('payment_checkout')


def perform_status_check_cash(sender, instance, **kwargs):
    if hasattr(instance, 'invoice'):
        payment_status = instance.invoice.payment_status
        ipi = InfringementPenaltyInvoice.objects.get(invoice_reference=instance.invoice.reference)
        so = ipi.infringement_penalty.sanction_outcome

        if payment_status == SanctionOutcome.PAYMENT_STATUS_PAID:
            so.payment_status = SanctionOutcome.PAYMENT_STATUS_PAID
            so.log_user_action(SanctionOutcomeUserAction.ACTION_PAY_INFRINGEMENT_PENALTY.format(so.lodgement_number, instance.amount, instance.invoice.reference), '(internal)')
            so.close()
        elif payment_status == SanctionOutcome.PAYMENT_STATUS_UNPAID:
            so.payment_status = SanctionOutcome.PAYMENT_STATUS_UNPAID
            so.save()
        elif payment_status == SanctionOutcome.PAYMENT_STATUS_PARTIALLY_PAID:
            so.payment_status = SanctionOutcome.PAYMENT_STATUS_PARTIALLY_PAID
            so.save()
            so.log_user_action(SanctionOutcomeUserAction.ACTION_PAY_INFRINGEMENT_PENALTY.format(so.lodgement_number, instance.amount, instance.invoice.reference), '(internal)')
        elif payment_status == SanctionOutcome.PAYMENT_STATUS_OVER_PAID:
            so.payment_status = SanctionOutcome.PAYMENT_STATUS_OVER_PAID
            so.save()
            so.log_user_action(SanctionOutcomeUserAction.ACTION_PAY_INFRINGEMENT_PENALTY.format(so.lodgement_number, instance.amount, instance.invoice.reference), '(internal)')
    else:
        logger.warn('CashTransaction: {} saved without any invoice'.format(instance))


post_save.connect(perform_status_check_cash, sender=CashTransaction)  # To catch 'Record Payment'
# post_save.connect(perform_status_check_cc, sender=BpointTransaction)  # To catch CC transaction
