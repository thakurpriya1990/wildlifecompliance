from oscar.apps.checkout.utils import CheckoutSessionData as CoreCheckoutSessionData

class CheckoutSessionData(CoreCheckoutSessionData):
    # Custom Ledger methods

    # Card Methods
    # ===========================
    def charge_by(self, method):
        self._set('ledger','card',method)

    def card_method(self):
        return self._get('ledger','card')

    # Return URL Methods
    # ===========================
    def return_to(self, url):
        self._set('ledger','return_url',url)

    def return_url(self):
        return self._get('ledger','return_url')

    # Template Methods
    # ===========================
    def use_template(self, url):
        self._set('ledger','custom_template_url',url)

    def custom_template(self):
        return self._get('ledger','custom_template_url')

    # System Methods
    # ===========================
    def use_system(self, system_id):
        self._set('ledger','system_id',system_id)
        
    def system(self):
        return self._get('ledger','system_id')
    
    # Aplication Methods
    # ===========================
    def use_application(self, _id):
        self._set('ledger','app_id',_id)
 
    def application(self):
        return self._get('ledger','app_id')

    # BPAY Methods
    # ===========================
    def bpay_using(self, method):
        self._set('ledger','bpay_method',method)
 
    def bpay_method(self):
        return self._get('ledger','bpay_method')

    # BPAY ICRN Format
    # ===========================
    def icrn_using(self, _format):
        self._set('ledger', 'icrn_format',_format)

    def icrn_format(self):
        return self._get('ledger','icrn_format')

    # Basket owner
    # ===========================
    def owned_by(self, user_id):
        self._set('ledger','basket_owner',user_id)

    def basket_owner(self):
        return self._get('ledger','basket_owner')

    # BPAY due date
    # ===========================
    def bpay_by(self, due_date):
        self._set('ledger','due_date',due_date)

    def bpay_due(self):
        return self._get('ledger','due_date')

    # Checkout using Token
    # ===========================
    def checkout_using_token(self, status):
        self._set('ledger','checkout_by_token',status)

    def checkoutWithToken(self):
        return self._get('ledger','checkout_by_token')

    # Associate token to invoice
    # ===========================
    def associate_invoice(self, status):
        self._set('ledger','associate_invoice',status)

    def invoice_association(self):
        return self._get('ledger','associate_invoice')

    # Store Card
    # ===========================
    def permit_store_card(self, status):
        self._set('ledger','store_card',status)

    def store_card(self):
        return self._get('ledger','store_card')

    # Redirection
    # ===========================
    def redirect_forcefully(self, status):
        self._set('ledger','force_redirect',status)

    def force_redirect(self):
        return self._get('ledger','force_redirect')

    # Basket Free
    # ===========================
    def is_free_basket(self, status):
        self._set('ledger','free_basket',status)

    def free_basket(self):
        return self._get('ledger','free_basket')

    # Email
    # ===========================
    def return_email(self, status):
        self._set('ledger','send_email',status)

    def send_email(self):
        return self._get('ledger','send_email')