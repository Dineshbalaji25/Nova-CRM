from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0006_alter_blueprint_options_alter_workflow_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflow',
            name='last_executed_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Last time this scheduled workflow was triggered',
            ),
        ),
    ]
