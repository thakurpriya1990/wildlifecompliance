# from django.http import HttpResponseRedirect
# from django.core.urlresolvers import reverse
# from django.conf import settings
# from django.core.exceptions import ValidationError
# from django.db import transaction

from datetime import datetime, timedelta, date
# from django.utils import timezone
# from dateutil.relativedelta import relativedelta
# from commercialoperator.components.main.models import Park
# from commercialoperator.components.proposals.models import Proposal
# from commercialoperator.components.organisations.models import Organisation
# from commercialoperator.components.bookings.models import Booking, ParkBooking, BookingInvoice, ApplicationFee
# from commercialoperator.components.bookings.email import send_monthly_invoice_tclass_email_notification
# from ledger.checkout.utils import create_basket_session, create_checkout_session, calculate_excl_gst
from ledger.payments.models import Invoice
# from ledger.payments.utils import oracle_parser
# import json
# import ast
from decimal import Decimal

import logging

from wildlifecompliance.components.wc_payments.models import InfringementPenalty

logger = logging.getLogger('payment_checkout')

def get_session_infringement_invoice(session):
    """ Infringement Penalty session ID """
    if 'wc_infringement_invoice' in session:
        wc_infringement_id = session['wc_infringement_invoice']
    else:
        raise Exception('Infringement Penalty not in Session')

    try:
        return InfringementPenalty.objects.get(id=wc_infringement_id)
    except Invoice.DoesNotExist:
        raise Exception('Infringement Penalty not found for Sanction Outcome {}'.format(wc_infringement_id))

def set_session_infringement_invoice(session, infringement_penalty):
    """ Infringement Penalty session ID """
    session['wc_infringement_invoice'] = infringement_penalty.id
    session.modified = True

def delete_session_infringement_invoice(session):
    """ Infringement Penalty session ID """
    if 'wc_infringement_invoice' in session:
        del session['wc_infringement_invoice']
        session.modified = True

def create_infringement_lines(sanction_outcome, invoice_text=None, vouchers=[], internal=False):
    """ Create the ledger lines - line item for infringement penalty sent to payment system """

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    line_items = [
        {   'ledger_description': 'Infringement Penalty - {} - {}'.format(now, 11111 ),
            'oracle_code': 'ABC123 GST',
            'price_incl_tax':  Decimal(100.00),
            'price_excl_tax':  Decimal(100.00),
            'quantity': 2,
        },
    ]
    logger.info('{}'.format(line_items))
    return line_items

#def _create_fee_lines(proposal, invoice_text=None, vouchers=[], internal=False):
#    """ Create the ledger lines - line item for application fee sent to payment system """
#
#    now = datetime.now().strftime('%Y-%m-%d %H:%M')
#    application_price = proposal.application_type.application_fee
#    licence_price = proposal.licence_fee_amount
#    line_items = [
#        {   'ledger_description': 'Application Fee - {} - {}'.format(now, proposal.lodgement_number),
#            'oracle_code': proposal.application_type.oracle_code_application,
#            'price_incl_tax':  application_price,
#            'price_excl_tax':  application_price if proposal.application_type.is_gst_exempt else calculate_excl_gst(application_price),
#            'quantity': 1,
#        },
#    ]
#    logger.info('{}'.format(line_items))
#    return line_items


