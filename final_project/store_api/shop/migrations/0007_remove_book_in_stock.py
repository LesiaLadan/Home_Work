from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0006_alter_book_options"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="book",
            name="in_stock",
        ),
    ]
