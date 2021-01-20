from django.core.management.base import BaseCommand

import logging

from wildlifecompliance.components.applications.models import ApplicationStandardCondition, ApplicationSelectedActivityPurpose
from wildlifecompliance.components.licences.models import PurposeSpecies
from wildlifecompliance.components.licences.pdf import styles, html_to_rl

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Extend original due date to 2nd due date'

    def handle(self, *args, **options):
        errors_text = []
        errors_info = [] 
        errors_species = [] 
        errors_species2 = [] 

        for sc in ApplicationStandardCondition.objects.all():
            try:
                html_to_rl(sc.text, styles)
            except Exception as e:
                logger.error('ApplicationStandardCondition (text): {}'.format(e))
                errors_text.append(sc.id)

            
        for sc in ApplicationStandardCondition.objects.all():
            try:
                html_to_rl(sc.additional_information, styles)
            except Exception as e:
                logger.error('ApplicationStandardCondition (additional_info): {}'.format(e))
                errors_info.append(sc.id)

        for ps in PurposeSpecies.objects.all():
            try:
                html_to_rl(ps.details, styles)
            except Exception as e:
                logger.error('PurposeSpecies (details): {}'.format(e))
                errors_species.append(ps.id)
            
        for i in ApplicationSelectedActivityPurpose.objects.all():
            for j in i.purpose_species_json:
                try:
                    html_to_rl(j['details'], styles)
                except Exception as e:
                    logger.error('ApplicationSelectedActivityPurpose (details - post Propose Issue action): {}'.format(e))
                    errors_species2.append(i.id)

        print('\n\nerrors_text IDs (ApplicationStandardCondition): {}\nerrors_info IDs (ApplicationStandardCondition): {}\nerrors_species IDsi (PurposeSpecies): {}\nerrors_species2 IDs (ApplicationSelectedActivityPurpose): {}\n'.format(errors_text, errors_info, errors_species, errors_species2))

