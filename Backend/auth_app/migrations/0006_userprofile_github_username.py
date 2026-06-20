# Generated migration for adding github_username field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0005_remove_message_conversation_delete_conversation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='github_username',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
