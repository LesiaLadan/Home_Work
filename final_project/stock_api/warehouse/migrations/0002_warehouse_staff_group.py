from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations


def create_warehouse_staff_group(apps, schema_editor):
    # Permission objects for a model are normally created by Django's
    # post_migrate signal, which only fires once *after* the whole
    # `migrate` run finishes - too late for this data migration to see
    # them. Create them explicitly first.
    app_config = global_apps.get_app_config("warehouse")
    create_permissions(app_config, apps=apps, verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    stock_item_ct = ContentType.objects.get(app_label="warehouse", model="stockitem")
    permissions = Permission.objects.filter(
        content_type=stock_item_ct,
        codename__in=["view_stockitem", "add_stockitem", "change_stockitem"],
    )

    group, _ = Group.objects.get_or_create(name="warehouse_staff")
    group.permissions.set(permissions)


def remove_warehouse_staff_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="warehouse_staff").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("warehouse", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_warehouse_staff_group, remove_warehouse_staff_group
        ),
    ]
