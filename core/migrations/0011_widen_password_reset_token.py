from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_pushtoken'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='password_reset_token',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
