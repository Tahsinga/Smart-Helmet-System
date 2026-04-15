# Generated migration for adding humidity field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0002_alter_sensordata_latitude_alter_sensordata_longitude'),
    ]

    operations = [
        migrations.AddField(
            model_name='sensordata',
            name='humidity',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
