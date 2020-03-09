from django_cron import CronJobBase, Schedule

from wildlifecompliance.components.applications.service import (
    ApplicationService
)


class VerifyLicenceSpeciesJob(CronJobBase):
    """
    Verifies LicenceSpecies against TSC server.
    """
    RUN_AT_TIMES = ['00:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'applications.verify_licence_species'

    def do(self):
        ApplicationService.verify_licence_species()
