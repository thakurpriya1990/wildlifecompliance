from django_cron import CronJobBase, Schedule


class VerifyLicenceSpeciesJob(CronJobBase):
    """
    Verifies LicenceSpecies against TSC server.
    """
    RUN_AT_TIMES = ['00:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'applications.verify_licence_species'

    def do(self):
        pass
