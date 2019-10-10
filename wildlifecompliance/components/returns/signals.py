from django.dispatch import receiver
from django.db.models.signals import post_save
from django.conf import settings

from wildlifecompliance.components.returns.models import (
    Return,
    ReturnType,
)

class ReturnsListener(object):
    """
    Listener object signalling additional processing outside Return model.
    """
    @staticmethod
    @receiver(post_save, sender=Return)
    def post_create(sender, instance, created, **kwargs):
        if not created:
            return
        if instance.has_sheet:
            # create default species data for Return running sheets.
            instance.sheet.set_licence_species
