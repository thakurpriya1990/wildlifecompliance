import traceback
from django.views.generic.base import TemplateView
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from wildlifecompliance.components.returns.utils import (
    get_session_return,
    delete_session_return,
    bind_return_to_invoice,
)
from wildlifecompliance.components.returns.email import (
    send_return_invoice_notification,
)


class ReturnSuccessView(TemplateView):
    template_name = 'wildlifecompliance/returns_success.html'

    def get(self, request, *args, **kwargs):
        print('returns success view')
        try:
            print(get_session_return(request.session))
            returns = get_session_return(request.session)
            invoice_ref = request.GET.get('invoice')
            try:
                bind_return_to_invoice(request, returns, invoice_ref)

                invoice_url = request.build_absolute_uri(
                    reverse('payments:invoice-pdf',
                            kwargs={'reference': invoice_ref})
                )

                if returns.return_fee_paid:

                    returns.set_submitted(request)
                    send_return_invoice_notification(
                        returns, invoice_ref, request
                    )
                else:
                    # TODO: check if this ever occurs from the
                    # above code and provide error screen for user.
                    delete_session_return(request.session)
                    return redirect(reverse('external'))

            except Exception as e:
                print(e)
                traceback.print_exc
                delete_session_return(request.session)
                return redirect(reverse('external'))

        except Exception as e:
            print(e)
            traceback.print_exc
            delete_session_return(request.session)
            return redirect(reverse('external'))

        context = {
            'return': returns,
            'invoice_ref': invoice_ref,
            'invoice_url': invoice_url
        }
        delete_session_return(request.session)
        return render(request, self.template_name, context)
