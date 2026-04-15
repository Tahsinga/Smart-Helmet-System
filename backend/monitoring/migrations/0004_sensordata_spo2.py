# Generated migration for adding spo2 field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0003_sensordata_humidity'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensordata',
            name='spo2',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]
