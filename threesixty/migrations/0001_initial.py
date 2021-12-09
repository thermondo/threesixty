# Generated by Django 2.0.2 on 2018-02-06 15:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Answer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("decision", models.BooleanField(verbose_name="decision")),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
            ],
            options={
                "ordering": ("-created",),
                "get_latest_by": "created",
            },
        ),
        migrations.CreateModel(
            name="Participant",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("email", models.EmailField(max_length=254, verbose_name="email")),
                (
                    "relation",
                    models.CharField(
                        choices=[
                            ("self", "self"),
                            ("subordinate", "subordinate"),
                            ("peer", "peer"),
                            ("supervisor", "supervisor"),
                        ],
                        max_length=11,
                        verbose_name="relation",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "text",
                    models.CharField(
                        db_index=True,
                        max_length=79,
                        unique=True,
                        verbose_name="question",
                    ),
                ),
                (
                    "attribute",
                    models.CharField(
                        db_index=True, max_length=30, verbose_name="attribute"
                    ),
                ),
                (
                    "connotation",
                    models.BooleanField(
                        choices=[(True, "positive"), (False, "negative")],
                        default=True,
                        verbose_name="connotation",
                    ),
                ),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
            ],
            options={
                "ordering": ("-created",),
                "get_latest_by": "created",
            },
        ),
        migrations.CreateModel(
            name="Survey",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "employee_name",
                    models.CharField(max_length=30, verbose_name="employee name"),
                ),
                (
                    "employee_gender",
                    models.CharField(
                        choices=[
                            ("female", "female"),
                            ("male", "male"),
                            ("other", "other"),
                        ],
                        default="other",
                        max_length=6,
                        verbose_name="employee gender",
                    ),
                ),
                (
                    "employee_email",
                    models.EmailField(max_length=254, verbose_name="employee email"),
                ),
                (
                    "manager_email",
                    models.EmailField(max_length=254, verbose_name="manager email"),
                ),
                (
                    "created",
                    models.DateTimeField(auto_now_add=True, verbose_name="created"),
                ),
            ],
        ),
        migrations.AddField(
            model_name="participant",
            name="survey",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                to="threesixty.Survey",
            ),
        ),
        migrations.AddField(
            model_name="answer",
            name="participant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="threesixty.Participant"
            ),
        ),
        migrations.AddField(
            model_name="answer",
            name="question",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="threesixty.Question"
            ),
        ),
        migrations.AddField(
            model_name="answer",
            name="survey",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="threesixty.Survey"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="participant",
            unique_together={("email", "survey")},
        ),
        migrations.AlterUniqueTogether(
            name="answer",
            unique_together={("survey", "question", "participant")},
        ),
    ]
