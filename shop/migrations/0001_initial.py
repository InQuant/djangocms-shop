# Generated by Django 2.2.12 on 2020-08-06 10:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import filer.fields.file
import shop.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('post_office', '0008_attachment_headers'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('filer', '0011_auto_20190418_0137'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('transition_target', models.CharField(max_length=50, verbose_name='Event')),
                ('notify', shop.models.fields.ChoiceEnumField(verbose_name='Whom to notify')),
                ('mail_template', models.ForeignKey(limit_choices_to=models.Q(('language__isnull', True), ('language', ''), _connector='OR'), on_delete=django.db.models.deletion.CASCADE, to='post_office.EmailTemplate', verbose_name='Template')),
                ('recipient', models.ForeignKey(limit_choices_to={'is_staff': True}, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Recipient')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'ordering': ['transition_target', 'recipient_id'],
            },
        ),
        migrations.CreateModel(
            name='NotificationAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment', filer.fields.file.FilerFileField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_attachment', to='filer.File')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.Notification')),
            ],
        ),
    ]
