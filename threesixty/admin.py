from django.contrib import admin

from . import models


class ParticipantInlineAdmin(admin.TabularInline):
    model = models.Participant


@admin.register(models.Survey)
class SurveyAdmin(admin.ModelAdmin):
    inlines = [ParticipantInlineAdmin]


admin.site.register(models.Question)
