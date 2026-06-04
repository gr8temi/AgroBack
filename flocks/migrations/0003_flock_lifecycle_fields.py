from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flocks', '0002_flock_farm'),
    ]

    operations = [
        migrations.AddField(
            model_name='flock',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('closed', 'Closed')], default='active', max_length=10),
        ),
        migrations.AddField(
            model_name='flock',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='flock',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='flock',
            name='closure_reason',
            field=models.CharField(blank=True, choices=[('sold', 'Sold'), ('culled', 'Culled'), ('disposed', 'Disposed'), ('transferred', 'Transferred'), ('other', 'Other')], max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='flock',
            name='closure_notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='flock',
            name='total_eggs_collected',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='flock',
            name='total_feed_kg',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='flock',
            name='total_feed_cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='flock',
            name='total_health_cost',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='flock',
            name='total_mortality',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='flock',
            name='total_income',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='flock',
            name='total_expense',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddIndex(
            model_name='flock',
            index=models.Index(fields=['farm', 'status'], name='flocks_flock_farm_id_status_idx'),
        ),
    ]
