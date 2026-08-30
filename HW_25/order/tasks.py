from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from datetime import datetime
from django.db.models import Sum
from order.models import Order


@shared_task
def send_order_confirmation_email(
    order_id, user_name, user_email, total_price, payment_method
):
    send_mail(
        subject=f"Order #{order_id} created",
        message=(
            f"Hello, {user_name}!\n\n"
            f"Thank you for your order.\n\n"
            f"Order number: {order_id}\n"
            f"Total amount: {total_price} UAH\n"
            f"Payment method: {payment_method}\n\n"
            f"We will notify you when your order is processed."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False,
    )


@shared_task
def generate_orders_report():
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum("total_price"))["total"] or 0

    report_text = (
        f"Orders report — {datetime.now():%Y-%m-%d %H:%M}\n"
        f"Total orders: {total_orders}\n"
        f"Total revenue: {total_revenue} UAH\n"
    )

    report_path = (
        settings.BASE_DIR
        / "reports"
        / f"orders_report_{datetime.now():%Y%m%d_%H%M%S}.txt"
    )
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report_text)

    return str(report_path)
