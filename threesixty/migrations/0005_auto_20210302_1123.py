# Generated by Django 3.1.7 on 2021-03-02 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('threesixty', '0004_survey_show_question_progress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='decision',
            field=models.BooleanField(null=True, verbose_name='decision'),
        ),
        migrations.AlterField(
            model_name='survey',
            name='show_question_progress',
            field=models.BooleanField(default=False, help_text='This option displays how many questions are completed out of the total amount questions.', verbose_name='show question progress'),
        ),
    ]