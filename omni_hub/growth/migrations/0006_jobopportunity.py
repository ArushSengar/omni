from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('growth', '0005_growthpost_growth_grow_created_a4412b_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobOpportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('company', models.CharField(max_length=255)),
                ('location', models.CharField(default='Remote', max_length=255)),
                ('url', models.CharField(blank=True, max_length=500)),
                ('source', models.CharField(default='RemoteOK', max_length=100)),
                ('role_type', models.CharField(default='Cybersecurity', max_length=100)),
                ('match_score', models.IntegerField(default=75)),
                ('matched_skills', models.CharField(blank=True, max_length=300)),
                ('salary', models.CharField(blank=True, max_length=100)),
                ('summary', models.TextField(blank=True)),
                ('tailored_pitch', models.TextField(blank=True, help_text="Bespoke human cover note tailored to Arush's profile")),
                ('status', models.CharField(choices=[('NEW', 'New Match'), ('REVIEWED', 'Reviewed'), ('APPLIED', 'Applied'), ('INTERVIEW', 'Interview'), ('ARCHIVED', 'Archived')], default='NEW', max_length=50)),
                ('detected_at', models.DateTimeField(auto_now_add=True)),
                ('applied_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-match_score', '-detected_at'],
            },
        ),
        migrations.AddIndex(
            model_name='jobopportunity',
            index=models.Index(fields=['-match_score'], name='growth_jobo_match_s_2d8f73_idx'),
        ),
        migrations.AddIndex(
            model_name='jobopportunity',
            index=models.Index(fields=['status'], name='growth_jobo_status_a60480_idx'),
        ),
        migrations.AddIndex(
            model_name='jobopportunity',
            index=models.Index(fields=['role_type'], name='growth_jobo_role_ty_e93ffc_idx'),
        ),
        migrations.AddIndex(
            model_name='jobopportunity',
            index=models.Index(fields=['-detected_at'], name='growth_jobo_detecte_47b302_idx'),
        ),
    ]

