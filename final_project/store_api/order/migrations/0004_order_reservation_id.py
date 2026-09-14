from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0003_alter_order_payment_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="reservation_id",
            field=models.CharField(
                blank=True,
                help_text="Id of the matching reservation in stock_api",
                max_length=36,
                null=True,
                verbose_name="Stock reservation id",
            ),
        ),
    ]
