from django.db import migrations, models


def backfill_start_date(apps, schema_editor):
    Flock = apps.get_model('flocks', 'Flock')
    Flock.objects.filter(start_date__isnull=True).update(
        start_date=models.F('date_added')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0003_flock_lifecycle_fields'),
    ]

    operations = [
        migrations.RunPython(backfill_start_date, migrations.RunPython.noop),
    ]
