from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("webhooks", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="webhookevent",
            name="event_id",
            field=models.CharField(db_index=True, max_length=64),
        ),
        migrations.AddConstraint(
            model_name="webhookevent",
            constraint=models.UniqueConstraint(
                fields=("provider_message_id", "event_id"),
                name="uniq_provider_message_event",
            ),
        ),
    ]
