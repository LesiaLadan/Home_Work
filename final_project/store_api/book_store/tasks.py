from celery import shared_task
from django.core.management import call_command


@shared_task
def cleanup_expired_sessions():
    call_command("clearsessions")
