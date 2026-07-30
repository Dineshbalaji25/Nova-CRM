from django.db import migrations, models
import django.db.models.deletion
import encrypted_model_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('omnichannel', '0004_supportchatmessage'),
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='calllog',
            name='deal',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='calls',
                to='crm.deal',
            ),
        ),
        migrations.AlterField(
            model_name='phoneintegration',
            name='auth_token',
            field=encrypted_model_fields.fields.EncryptedCharField(max_length=255),
        ),
    ]
