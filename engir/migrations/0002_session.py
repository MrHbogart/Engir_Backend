from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('engir', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=140)),
                ('description', models.TextField(blank=True)),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField(blank=True, null=True)),
                ('duration_minutes', models.PositiveIntegerField(default=45)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('live', 'Live'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='scheduled', max_length=20)),
                ('stream_provider', models.CharField(choices=[('custom', 'Custom RTMP'), ('zoom', 'Zoom'), ('google_meet', 'Google Meet'), ('youtube', 'YouTube Live'), ('other', 'Other')], default='custom', max_length=20)),
                ('stream_key', models.CharField(blank=True, max_length=64)),
                ('host_url', models.URLField(blank=True)),
                ('playback_url', models.URLField(blank=True)),
                ('recording_url', models.URLField(blank=True)),
                ('meeting_passcode', models.CharField(blank=True, max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='engir.classroom')),
            ],
            options={
                'ordering': ['starts_at'],
            },
        ),
    ]
