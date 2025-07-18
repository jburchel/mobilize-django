# Generated by Django 4.2 on 2025-06-16 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="pipeline_stage",
            field=models.CharField(
                blank=True,
                choices=[
                    ("confirmation", "Confirmation"),
                    ("automation", "Automation"),
                    ("invitation", "Invitation"),
                    ("en42", "EN42"),
                    ("information", "Information"),
                    ("promotion", "Promotion"),
                ],
                help_text="Current stage in the engagement pipeline.",
                max_length=50,
                null=True,
            ),
        ),
    ]
