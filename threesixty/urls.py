from django.contrib import admin
from django.urls import path
from django.views import generic

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", generic.TemplateView.as_view(template_name="index.html"), name="index"),
    path(
        "thanks",
        generic.TemplateView.as_view(template_name="threesixty/thanks.html"),
        name="thanks",
    ),
    path("create", views.SurveyCreateView.as_view(), name="survey-create"),
    path("<int:pk>/<token>/view", views.SurveyDetailView.as_view(), name="survey-view"),
    path("<int:pk>/<token>/edit", views.SurveyUpdateView.as_view(), name="survey-edit"),
    path("<int:pk>/<token>/data", views.SurveyDataView.as_view(), name="survey-data"),
    path(
        "<int:survey_pk>/<token>/invite",
        views.ParticipantCreateView.as_view(),
        name="survey-invite",
    ),
    path(
        "<int:survey_pk>/<token>/answer",
        views.AnswerCreateView.as_view(),
        name="survey-answer",
    ),
    path(
        "<int:survey_pk>/<token>/answer/<int:question_pk>",
        views.AnswerCreateView.as_view(),
        name="surver-answer-specific",
    ),
]
