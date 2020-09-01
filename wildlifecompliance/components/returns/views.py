import traceback
from django.db import transaction
from django.views.generic.base import TemplateView
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from wildlifecompliance.components.returns.utils import (
    get_session_return,
    delete_session_return,
)
from wildlifecompliance.components.returns.services import ReturnService


class ReturnSuccessView(TemplateView):
    template_name = 'wildlifecompliance/returns_success.html'

    def get(self, request, *args, **kwargs):
        context = None
        try:
            with transaction.atomic:
                the_return = get_session_return(request.session)
                # When submission is successful the payment can be invoiced.
                # When unsuccessful invoicing, the Return is submitted but
                # unpaid.
                ReturnService.submit_session_return_request(request)
                ReturnService.invoice_session_return_request(request)

            invoice_ref = request.GET.get('invoice')
            invoice_url = request.build_absolute_uri(
                reverse('payments:invoice-pdf',
                        kwargs={'reference': invoice_ref})
            )
            context = {
                'return': the_return,
                'invoice_ref': invoice_ref,
                'invoice_url': invoice_url
            }
            delete_session_return(request.session)

        except BaseException:
            delete_session_return(request.session)
            traceback.print_exc
            return redirect(reverse('external'))

        return render(request, self.template_name, context)


class ReturnSheetSuccessView(TemplateView):
    template_name = 'wildlifecompliance/returns_success.html'

    def get(self, request, *args, **kwargs):
        context = None
        try:
            the_return = get_session_return(request.session)
            # When submission is successful the payment can be invoiced. When
            # unsuccessful invoicing, the Return is submitted but unpaid.
            # ReturnService.submit_session_return_request(request)
            ReturnService.invoice_session_return_request(request)

            invoice_ref = request.GET.get('invoice')
            invoice_url = request.build_absolute_uri(
                reverse('payments:invoice-pdf',
                        kwargs={'reference': invoice_ref})
            )
            context = {
                'return': the_return,
                'invoice_ref': invoice_ref,
                'invoice_url': invoice_url
            }
            delete_session_return(request.session)

        except BaseException:
            delete_session_return(request.session)
            traceback.print_exc
            return redirect(reverse('external'))

        return render(request, self.template_name, context)
