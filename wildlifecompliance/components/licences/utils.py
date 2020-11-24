import logging

logger = logging.getLogger(__name__)
# logger = logging


class LicencePurposeUtil(object):
    """
    Helper utility for Licence Purpose.
    """
    licence = None

    def __init__(self, purpose):
        self.licence = purpose

    def is_valid_age_for(self, user):
        '''
        Check user date of birth minimum age required for licence.
        '''
        from datetime import date
        logger.debug('LicencePurposeUtil.is_valid_age_for() - start')
        valid = False
        today = date.today()
        # calculate age within the year.
        # yy = 1 if ((today.month, today.day) < born.month, born.day)) else 0
        # age = today.year - born.year - yy
        difference = (today.year - user.dob.year - (
            (today.month, today.day) < (user.dob.month, user.dob.day)
        )) - self.licence.minimum_age
        valid = True if difference > -1 else False

        logger.debug('LicencePurposeUtil.is_valid_age_for() - end')
        return valid
