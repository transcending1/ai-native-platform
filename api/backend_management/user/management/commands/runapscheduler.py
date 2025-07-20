import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore

from llm_api.settings.prod_settings import error_logger, info_logger
from user.cron.clean_logs import clean_logs

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Runs APScheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            clean_logs,
            trigger=CronTrigger(day_of_week="mon", hour="00", minute="00"),
            id="clean_logs",
            max_instances=1,
            replace_existing=True,
        )

        try:
            info_logger("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            error_logger("Stopping scheduler...")
            scheduler.shutdown()
            error_logger("Scheduler shut down successfully!")
