from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic.base import View, TemplateView
from django.db import transaction
from ledger.payments.helpers import is_payment_admin
from ledger.payments.pdf import create_invoice_pdf_bytes
from ledger.payments.utils import update_payments
from ledger.payments.models import Invoice
from ledger.basket.models import Basket
from ledger.payments.mixins import InvoiceOwnerMixin
from oscar.apps.order.models import Order
import logging
from wildlifecompliance.components.wc_payments.context_processors import template_context
from wildlifecompliance.components.wc_payments.models import InfringementPenalty, InfringementPenaltyInvoice
from wildlifecompliance.components.wc_payments.utils import set_session_infringement_invoice, \
    get_session_infringement_invoice, delete_session_infringement_invoice, checkout, create_other_invoice
from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, SanctionOutcomeUserAction
from wildlifecompliance.settings import PS_PAYMENT_SYSTEM_ID, WC_PAYMENT_SYSTEM_ID

logger = logging.getLogger('payment_checkout')


class InfringementPenaltyView(TemplateView):
    template_name = 'wildlifecompliance/wc_payments/success.html'

    def get_object(self):
        return get_object_or_404(SanctionOutcome, id=self.kwargs['sanction_outcome_id'])

    def post(self, request, *args, **kwargs):

        sanction_outcome = self.get_object()
        if not sanction_outcome.infringement_penalty:
            sanction_outcome.infringement_penalty = InfringementPenalty.objects.create(created_by=request.user, payment_type=InfringementPenalty.PAYMENT_TYPE_TEMPORARY)
        sanction_outcome.save()

        try:
            with transaction.atomic():
                set_session_infringement_invoice(request.session, sanction_outcome.infringement_penalty)
                lines = sanction_outcome.as_line_items
                checkout_response = checkout(
                    request,
                    sanction_outcome,
                    lines,
                    return_url_ns='penalty_success',
                    return_preload_url_ns='penalty_success',
                    invoice_text='Infringement Notice'
                )

                logger.info('{} built payment line item {} for Infringement and handing over to payment gateway'.format('User {} with id {}'.format(request.user.get_full_name(), request.user.id), sanction_outcome.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Infringement Penalty: {}'.format(e))
            if sanction_outcome.infringement_penalty:
                sanction_outcome.infringement_penalty = None
            raise


# from commercialoperator.components.proposals.utils import proposal_submit
class InfringementPenaltySuccessView(TemplateView):
    template_name = 'wildlifecompliance/wc_payments/success.html'

    def get(self, request, *args, **kwargs):
        print ("=== Infringement Penalty SUCCESS ===")

        sanction_outcome = None
        offender = None
        invoice = None

        try:
            context = template_context(self.request)
            basket = None
            infringement_penalty = get_session_infringement_invoice(request.session)  # this raises an error when accessed 2nd time
            sanction_outcome = infringement_penalty.sanction_outcome

            recipient = sanction_outcome.get_offender()[0].email
            submitter = sanction_outcome.get_offender()[0]

            if self.request.user.is_authenticated():
                basket = Basket.objects.filter(status='Submitted', owner=request.user).order_by('-id')[:1]
            else:
                # basket = Basket.objects.filter(status='Submitted', owner=booking.proposal.submitter).order_by('-id')[:1]
                basket = Basket.objects.filter(status='Submitted', owner=None).order_by('-id')[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)

            print('invoice.reference: ' + invoice.reference)

            # Update status of the infringement notice
            if sanction_outcome.status not in SanctionOutcome.FINAL_STATUSES:
                inv_payment_status = invoice.payment_status
                if inv_payment_status == SanctionOutcome.PAYMENT_STATUS_PAID:
                    sanction_outcome.log_user_action(SanctionOutcomeUserAction.ACTION_PAY_INFRINGEMENT_PENALTY.format(sanction_outcome.lodgement_number, invoice.payment_amount, invoice.reference), request)
                    sanction_outcome.payment_status = SanctionOutcome.PAYMENT_STATUS_PAID
                    sanction_outcome.close()
                elif inv_payment_status == SanctionOutcome.PAYMENT_STATUS_OVER_PAID:
                    # Should not reach here
                    logger.warn('{} overpaid an infringement penalty: {}'.format(
                        'User {} with id {}'.format(request.user.get_full_name(), request.user.id) if sanction_outcome.offender else 'An anonymous user',
                        sanction_outcome.lodgement_number
                    ))
                    sanction_outcome.payment_status = SanctionOutcome.PAYMENT_STATUS_OVER_PAID
                    sanction_outcome.save()
                elif inv_payment_status == SanctionOutcome.PAYMENT_STATUS_PARTIALLY_PAID:
                    # Should not reach here
                    logger.warn('{} partially paid an infringement penalty: {}'.format(
                        'User {} with id {}'.format(request.user.get_full_name(), request.user.id) if sanction_outcome.offender else 'An anonymous user',
                        sanction_outcome.lodgement_number
                    ))
                    sanction_outcome.payment_status = SanctionOutcome.PAYMENT_STATUS_OVER_PAID
                    sanction_outcome.save()

            # invoice_ref = invoice.reference
            fee_inv, created = InfringementPenaltyInvoice.objects.get_or_create(infringement_penalty=infringement_penalty, invoice_reference=invoice.reference)
            # infringement_penalty.invoice = invoice
            # infringement_penalty.save()

            if infringement_penalty.payment_type == InfringementPenalty.PAYMENT_TYPE_TEMPORARY:
                try:
                    # inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=invoice.order_number)
                    order.user = submitter
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an infringement penalty: {} with an incorrect invoice'.format(
                        'User {} with id {}'.format(request.user.get_full_name(), request.user.id) if request.user else 'An anonymous user',
                        sanction_outcome.lodgement_number
                    ))
                    #return redirect('external', args=(proposal.id,))
                    return redirect('external')

                if invoice.system not in [WC_PAYMENT_SYSTEM_ID.replace('S', '0'), PS_PAYMENT_SYSTEM_ID,]:
                    logger.error('{} tried paying an infringement penalty with an invoice from another system with reference number {}'.format(
                        'User {} with id {}'.format(request.user.get_full_name(), request.user.id) if request.user else 'An anonymous user',
                        invoice.reference
                    ))
                    #return redirect('external-proposal-detail', args=(proposal.id,))
                    return redirect('external')

                # if fee_inv:
                infringement_penalty.payment_type = InfringementPenalty.PAYMENT_TYPE_INTERNET
                infringement_penalty.expiry_time = None
                update_payments(invoice.reference)

                infringement_penalty.save()
                request.session['wc_last_infringement_invoice'] = infringement_penalty.id
                delete_session_infringement_invoice(request.session)
                print('delete session infringement invoice')

                # TODO 1. offender, 2. internal officer
                #send_application_fee_invoice_tclass_email_notification(request, proposal, invoice, recipients=[recipient])
                #send_application_fee_confirmation_tclass_email_notification(request, application_fee, invoice, recipients=[recipient])
                try:
                    invoice_created_datetime = invoice.created
                except Exception as e:
                    inv = Invoice.objects.get(reference=invoice.invoice_reference)
                    invoice_created_datetime = inv.created

                context = {
                    'sanction_outcome': sanction_outcome,
                    'offender': recipient,
                    'invoice_created_datetime': invoice_created_datetime
                }
                return render(request, self.template_name, context)

        except Exception as e:
            print('Exception: ' + e.message)
            if ('wc_last_infringement_invoice' in request.session) and InfringementPenalty.objects.filter(id=request.session['wc_last_infringement_invoice']).exists():
                infringement_penalty = InfringementPenalty.objects.get(id=request.session['wc_last_infringement_invoice'])
                sanction_outcome = infringement_penalty.sanction_outcome

                recipient = sanction_outcome.get_offender()[0].email
                submitter = sanction_outcome.assigned_to.email if sanction_outcome.assigned_to else None

                if InfringementPenaltyInvoice.objects.filter(infringement_penalty=infringement_penalty).count() > 0:
                    ip_inv = InfringementPenaltyInvoice.objects.filter(infringement_penalty=infringement_penalty)
                    invoice = ip_inv[0]

                # if infringement_penalty.infringement_penalty_invoices.all().count():

            else:
                return redirect('external')

        try:
            invoice_created_datetime = invoice.created
        except Exception as e:
            inv = Invoice.objects.get(reference=invoice.invoice_reference)
            invoice_created_datetime = inv.created
            # invoice_created_datetime = infringement_penalty.created

        context = {
            'sanction_outcome': sanction_outcome,
            'offender': recipient,
            'invoice_created_datetime': invoice_created_datetime
        }
        return render(request, self.template_name, context)


class InvoicePDFView(InvoiceOwnerMixin, View):
    """
    This is not used, because an infringement notice can be an invoice.
    """
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs['reference'])
        response = HttpResponse(content_type='application/pdf')
        response.write(create_invoice_pdf_bytes('invoice.pdf',invoice))
        return response

    def get_object(self):
        invoice = get_object_or_404(Invoice, reference=self.kwargs['reference'])
        return invoice


class DeferredInvoicingPreviewView(TemplateView):
    template_name = 'wildlifecompliance/wc_payments/preview.html'

    def get(self, request, *args, **kwargs):
        payment_method = self.request.GET.get('method', 'other')
        context = template_context(self.request)
        sanction_outcome_id = int(kwargs['sanction_outcome_pk'])
        sanction_outcome = SanctionOutcome.objects.get(id=sanction_outcome_id)

        try:
            recipient = sanction_outcome.get_offender()[0].email
            submitter = sanction_outcome.get_offender()[0]
        except Exception as e:
            recipient = sanction_outcome.get_offender()[0].email
            submitter = sanction_outcome.get_offender()[0]

        # TODO: make sure the if-conditional below
        if is_payment_admin(request.user):
            try:
                lines = sanction_outcome.as_line_items
                # logger.info('{} Show Park Bookings Preview for BPAY/Other/monthly invoicing'.format('User {} with id {}'.format(proposal.submitter.get_full_name(),proposal.submitter.id), proposal.id))
                context.update({
                    'lines': lines,
                    # 'line_details': request.POST['payment'],
                    'sanction_outcome_id': sanction_outcome_id,
                    'submitter': submitter,
                    'payment_method': payment_method,
                })
                return render(request, self.template_name, context)

            except Exception as e:
                logger.error('Error creating record payment preview: {}'.format(e))
        else:
            logger.error('Error creating record payment preview for the sanction outcome: {}'.format(sanction_outcome.lodgement_number))
            raise


class DeferredInvoicingView(TemplateView):
    template_name = 'wildlifecompliance/wc_payments/success.html'

    def post(self, request, *args, **kwargs):
        payment_method = self.request.POST.get('method')
        context = template_context(self.request)
        sanction_outcome_id = int(kwargs['sanction_outcome_pk'])
        sanction_outcome = SanctionOutcome.objects.get(id=sanction_outcome_id)

        if is_payment_admin(request.user):
            try:
                # infringement_penalty, created = InfringementPenalty.objects.get_or_create(sanction_outcome=sanction_outcome)
                # infringement_penalty.created_by = request.user
                # infringement_penalty.payment_type = InfringementPenalty.PAYMENT_TYPE_RECEPTION
                # infringement_penalty.save()
                if not sanction_outcome.infringement_penalty:
                    sanction_outcome.infringement_penalty = InfringementPenalty.objects.create()
                sanction_outcome.infringement_penalty.created_by = request.user
                sanction_outcome.infringement_penalty.payment_type = InfringementPenalty.PAYMENT_TYPE_RECEPTION
                sanction_outcome.save()

                invoice_reference = None
                if sanction_outcome and payment_method == 'other':
                    invoice = create_other_invoice(request, sanction_outcome)
                    # fee_inv = create_other_invoice(request, sanction_outcome)
                    # invoice_reference = fee_inv.invoice_reference
                    # invoice = Invoice.objects.get(reference=fee_inv.invoice_reference)
                    logger.info('{} paid for sanction outcome: {} with payment method {}'.format(sanction_outcome.get_offender()[0].get_full_name(), sanction_outcome.lodgement_number, payment_method))

                    if payment_method == 'other':
                        if is_payment_admin(request.user):
                            return HttpResponseRedirect(reverse('payments:invoice-payment') + '?invoice={}'.format(invoice.reference))
                        else:
                            raise PermissionDenied

            except Exception as e:
                logger.error('Error Creating record payment: {}'.format(e))
                # if booking:
                #     booking.delete()
                raise
        else:
            logger.error('Error Creating record payment for Sanction Outcome: {}'.format(sanction_outcome.lodgement_number))
            raise

#     if isinstance(proposal.org_applicant, Organisation):
    #         try:
    #             if proposal.org_applicant.bpay_allowed and payment_method=='bpay':
    #                 booking_type = Booking.BOOKING_TYPE_INTERNET
    #             elif proposal.org_applicant.monthly_invoicing_allowed and payment_method=='monthly_invoicing':
    #                 booking_type = Booking.BOOKING_TYPE_MONTHLY_INVOICING
    #             #elif proposal.org_applicant.other_allowed and payment_method=='other':
    #             else:
    #                 booking_type = Booking.BOOKING_TYPE_RECEPTION
    #
    #             booking = create_booking(request, proposal, booking_type=booking_type)
    #             invoice_reference = None
    #             if booking and payment_method=='bpay':
    #                 # BPAY/OTHER invoice are created immediately. Monthly invoices are created later by Cron
    #                 ret = create_bpay_invoice(submitter, booking)
    #                 invoice_reference = booking.invoice.reference
    #
    #             if booking and payment_method=='other':
    #                 # BPAY/Other invoice are created immediately. Monthly invoices are created later by Cron
    #                 ret = create_other_invoice(submitter, booking)
    #                 invoice_reference = booking.invoice.reference
    #
    #             if booking and payment_method=='monthly_invoicing':
    #                 # For monthly_invoicing, invoice is created later by Cron. Now we only create a confirmation
    #                 ret = create_monthly_confirmation(submitter, booking)
    #
    #             logger.info('{} Created Park Bookings with payment method {} for Proposal ID {}'.format('User {} with id {}'.format(proposal.submitter.get_full_name(),proposal.submitter.id), payment_method, proposal.id))
    #             #send_monthly_invoicing_confirmation_tclass_email_notification(request, booking, invoice, recipients=[recipient])
    #             context.update({
    #                 'booking': booking,
    #                 'booking_id': booking.id,
    #                 'submitter': submitter,
    #                 'monthly_invoicing': True if payment_method=='monthly_invoicing' else False,
    #                 'invoice_reference': invoice_reference
    #             })
    #             if payment_method=='other':
    #                 if is_payment_admin(request.user):
    #                     return HttpResponseRedirect(reverse('payments:invoice-payment') + '?invoice={}'.format(invoice_reference))
    #                 else:
    #                     raise PermissionDenied
    #             else:
    #                 return render(request, self.template_name, context)
    #
    #
    #         except Exception, e:
    #             logger.error('Error Creating booking: {}'.format(e))
    #             if booking:
    #                 booking.delete()
    #             raise
    #     else:
    #         logger.error('Error Creating booking: {}'.format(e))
    #         raise