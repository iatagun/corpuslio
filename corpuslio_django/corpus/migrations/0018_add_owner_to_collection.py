from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('corpus', '0017_userprofile_password_reset_expires_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='owner',
            field=models.ForeignKey(
                settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                related_name='collections',
                null=True,
                blank=True,
                verbose_name='Sahip'
            ),
        ),
    ]
