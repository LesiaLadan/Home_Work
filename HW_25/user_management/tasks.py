from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from user_management.models import User


@shared_task
def generate_users_report():
    total_users = User.objects.count()
    week_ago = timezone.now() - timedelta(days=7)
    new_users = User.objects.filter(date_joined__gte=week_ago).count()

    report_text = (
        f"Users report — {datetime.now():%Y-%m-%d %H:%M}\n"
        f"Total users: {total_users}\n"
        f"New registrations (last 7 days): {new_users}\n"
    )

    report_path = (
        settings.BASE_DIR
        / "reports"
        / f"users_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
    )
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report_text)

    return str(report_path)
