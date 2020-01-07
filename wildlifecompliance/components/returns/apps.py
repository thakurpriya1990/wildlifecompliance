from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ReturnsConfig(AppConfig):
    name = 'wildlifecompliance.components.returns'
    verbose_name = _('returns')

    def ready(self):
        import wildlifecompliance.components.returns.signals