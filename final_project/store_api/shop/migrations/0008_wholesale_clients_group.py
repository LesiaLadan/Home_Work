from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations


def create_wholesale_clients_group(apps, schema_editor):
    # The `view_wholesale_price` permission is declared in Book.Meta but
    # Permission rows for it are normally created by Django's post_migrate
    # signal, which only fires *after* the whole `migrate` run finishes -
    # too late for this data migration to see it. Create it explicitly.
    app_config = global_apps.get_app_config("shop")
    create_permissions(app_config, apps=apps, verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    book_ct = ContentType.objects.get(app_label="shop", model="book")
    permission = Permission.objects.get(
        content_type=book_ct, codename="view_wholesale_price"
    )

    group, _ = Group.objects.get_or_create(name="wholesale_clients")
    group.permissions.add(permission)


def remove_wholesale_clients_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="wholesale_clients").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0007_remove_book_in_stock"),
    ]

    operations = [
        migrations.RunPython(
            create_wholesale_clients_group, remove_wholesale_clients_group
        ),
    ]
