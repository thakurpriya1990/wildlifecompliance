from datetime import date, timedelta

from django_cron import CronJobBase, Schedule

from ledger.payments.utils import oracle_parser

from wildlifecompliance import settings


def oracle_integration(date, override):
    oracle_parser(
        date,
        settings.WC_PAYMENT_SYSTEM_PREFIX,
        settings.SYSTEM_NAME,
        override=override
        )


class OracleIntegrationCronJob(CronJobBase):
    """
    To Test (shortly after RUN_AT_TIMES):
        ./manage_wc.py runcrons
    """
    RUN_AT_TIMES = [settings.CRON_RUN_AT_TIMES]

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'wlc.oracle_integration'

    def do(self):
        oracle_integration(str(date.today()-timedelta(days=1)), False)
