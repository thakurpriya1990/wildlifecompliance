from django.core.exceptions import PermissionDenied

from ledger.payments import helpers
from wildlifecompliance.helpers import is_able_to_view_sanction_outcome_pdf


class InvoiceOwnerMixin(object):
    
    def belongs_to(self, user, group_name):
        return helpers.belongs_to(user, group_name)

    def is_payment_admin(self,user):
        return helpers.is_payment_admin(user)

    def check_owner(self, user):
        ret_val = False
        if self.is_payment_admin(user):
            ret_val = True
        else:
            obj = self.get_object()
            if hasattr(obj, 'order'):
                if obj.order.user == user:
                    ret_val = True
            if hasattr(obj, 'offender'):
                if obj.offender.person == user:
                    ret_val = True

        return ret_val

        # return self.get_object().order.user == user or self.is_payment_admin(user)

    def dispatch(self, request, *args, **kwargs):
        if not self.check_owner(request.user):    
            raise PermissionDenied
        return super(InvoiceOwnerMixin, self).dispatch(request, *args, **kwargs)


class SanctionOutcomePdfMixin(object):
    def check_owner(self, user):
        ret_val = False
        if is_able_to_view_sanction_outcome_pdf(user):
            ret_val = True
        else:
            obj = self.get_object()
            if hasattr(obj, 'order'):
                if obj.order.user == user:
                    ret_val = True
            if hasattr(obj, 'offender'):
                if obj.offender.person == user:
                    ret_val = True

        return ret_val

        # return self.get_object().order.user == user or self.is_payment_admin(user)

    def dispatch(self, request, *args, **kwargs):
        if not self.check_owner(request.user):
            raise PermissionDenied
        return super(SanctionOutcomePdfMixin, self).dispatch(request, *args, **kwargs)
