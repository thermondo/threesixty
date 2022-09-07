import random
from collections import defaultdict
from decimal import Decimal

from django.core import signing
from django.core.mail import send_mail
from django.db import connection
from django.http import (
    Http404,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import generic

from . import forms, models


class WithEmailTokenMixin:
    def dispatch(self, request, *args, **kwargs):
        self.token = kwargs["token"]
        signer = signing.TimestampSigner()
        try:
            self.email = signer.unsign(self.token)
        except signing.BadSignature:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["token"] = self.token
        return context


class EmployeeRequiredMixin(WithEmailTokenMixin):
    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if self.email not in [obj.employee_email, obj.manager_email]:
            raise Http404
        return obj


class ManagerRequiredMixin(WithEmailTokenMixin):
    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if self.email != obj.manager_email:
            raise Http404
        return obj


class SurveyViewMixin:
    def dispatch(self, request, *args, **kwargs):
        self.survey = self.get_survey()
        return super().dispatch(request, *args, **kwargs)

    def get_survey(self):
        try:
            survey_pk = self.kwargs["survey_pk"]
        except KeyError:
            raise Http404
        return get_object_or_404(models.Survey, pk=survey_pk, is_complete=False)


class SurveyDetailView(EmployeeRequiredMixin, generic.DetailView):
    model = models.Survey


class SurveyUpdateView(ManagerRequiredMixin, generic.UpdateView):
    model = models.Survey
    fields = ["is_complete"]
    template_name_suffix = "_detail"


class SurveyDataView(EmployeeRequiredMixin, generic.DetailView):
    queryset = models.Survey.objects.filter(is_complete=True)
    survey_results = """
        WITH results AS (
            SELECT
              p.relation AS relation,
              q.attribute AS attribute,
            CASE
              WHEN q.connotation THEN a.decision::INT
              ELSE 1 - a.decision::INT
            END AS score
            FROM threesixty_answer a
            JOIN threesixty_survey s
              ON s.id = a.survey_id
            JOIN threesixty_question q
              ON q.id = a.question_id
            JOIN threesixty_participant p
              ON p.id = a.participant_id
            WHERE s.id = %s
        ), benchmark_results AS (
            SELECT
              p.relation AS relation,
              q.attribute AS attribute,
            CASE
              WHEN q.connotation THEN a.decision::INT
              ELSE 1 - a.decision::INT
            END AS score
            FROM threesixty_answer a
            JOIN threesixty_survey s
              ON s.id = a.survey_id
            JOIN threesixty_question q
              ON q.id = a.question_id
            JOIN threesixty_participant p
              ON p.id = a.participant_id
        )
        SELECT
          relation,
          attribute,
          avg(score) AS avg_score
        FROM results
        GROUP BY relation, attribute
        UNION ALL
        SELECT
          'total' AS relation,
          attribute,
          avg(score) AS avg_score
        FROM results
        WHERE relation != 'self'
        GROUP BY attribute
        UNION ALL
        SELECT
          'benchmark' AS relation,
          attribute,
          avg(score) AS avg_score
        FROM benchmark_results
        WHERE relation != 'self'
        GROUP BY attribute;
    """

    colors = {
        "supervisor": "rgba(255, 0, 0, 0.5)",
        "subordinate": "rgba(255, 255, 0, 0.5)",
        "peer": "rgba(0, 0, 255, 0.5)",
        "self": "rgba(0, 255, 255, 0.5)",
        "total": "rgba(255, 0, 255, 0.5)",
        "benchmark": "rgba(0, 0, 0, 0.25)",
    }

    def get_results(self):
        with connection.cursor() as cursor:
            cursor.execute(self.survey_results, params=[self.object.pk])
            survey_data = cursor.fetchall()

        data = defaultdict(dict)
        for relation, attribute, value in survey_data:
            data[relation][attribute] = value
        return data

    def transform_to_chart_js(self, data):
        labels = list(list(data.values())[0].keys())
        datasets = []
        for attr, values in data.items():
            dataset = [values[label] for label in labels]
            datasets.append(
                {"label": attr, "data": dataset, "backgroundColor": self.colors[attr]}
            )
        return {"labels": labels, "datasets": datasets}

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        data = self.transform_to_chart_js(self.get_results())
        return JsonResponse(
            data,
            json_dumps_params=dict(
                default=lambda o: float(o) if isinstance(o, Decimal) else o
            ),
        )


class ParticipantCreateView(EmployeeRequiredMixin, SurveyViewMixin, generic.CreateView):
    model = models.Participant
    fields = (
        "email",
        "relation",
    )

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.survey = self.survey
        self.object.save()
        self.send_invite()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "survey-view", kwargs={"pk": self.survey.pk, "token": self.token}
        )

    def send_invite(self):
        context = {
            "employee_name": self.survey.employee_name,
            "survey_url": self.request.build_absolute_uri(
                self.object.get_absolute_url()
            ),
        }
        subject = "360-degree feedback - %s" % self.survey.employee_name
        msg = render_to_string("threesixty/invite_email.txt", context)
        send_mail(
            subject=subject,
            message=msg,
            from_email=self.survey.manager_email,
            recipient_list=[self.object.email],
        )


class SurveyCreateView(generic.CreateView):
    model = models.Survey
    fields = [
        "employee_name",
        "employee_email",
        "employee_gender",
        "manager_email",
        "participant_can_skip",
        "show_question_progress",
    ]

    def form_valid(self, form):
        response = super().form_valid(form=form)
        self.send_manager_mail()
        self.send_employee_mail()
        return response

    def send_manager_mail(self):
        context = {
            "employee_name": self.object.employee_name,
            "survey_url": self.request.build_absolute_uri(
                self.object.get_manager_url()
            ),
        }
        subject = "360-degree feedback - %s" % self.object.employee_name
        msg = render_to_string("threesixty/manager_email.txt", context)
        send_mail(
            subject=subject,
            message=msg,
            from_email=self.object.manager_email,
            recipient_list=[self.object.manager_email],
        )

    def send_employee_mail(self):
        context = {
            "employee_name": self.object.employee_name,
            "survey_url": self.request.build_absolute_uri(
                self.object.get_employee_url()
            ),
        }
        subject = "360-degree feedback"
        msg = render_to_string("threesixty/employee_email.txt", context)
        send_mail(
            subject=subject,
            message=msg,
            from_email=self.object.manager_email,
            recipient_list=[self.object.employee_email],
        )


class AnswerCreateView(WithEmailTokenMixin, SurveyViewMixin, generic.CreateView):
    model = models.Answer
    form_class = forms.AnswerForm

    def post(self, request, *args, **kwargs):
        self.participant = get_object_or_404(
            models.Participant, email=self.email, survey=self.survey
        )
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.participant = get_object_or_404(
            models.Participant, email=self.email, survey=self.survey
        )
        question_pk = self.kwargs.get("question_pk", None)
        if question_pk:
            return self.get_specific_question(request, question_pk, args, kwargs)
        else:
            return self.get_random_question(request, args, kwargs)

    def get_specific_question(self, request, question_pk, args, kwargs):
        if self.participant.answer_set.filter(question__pk=question_pk).exists():
            return self.redirect_survey_answer(self.survey.pk, self.token)
        else:
            question = get_object_or_404(models.Question, pk=question_pk)
            self.question = question
            return super().get(request, args, kwargs)

    def get_random_question(self, request, args, kwargs):
        try:
            self.question = self.get_question()
        except models.Question.DoesNotExist:
            return HttpResponseRedirect(reverse("thanks"))
        else:
            return super().get(request, args, kwargs)

    def get_question(self):
        answered = self.participant.answer_set.all().values_list(
            "question_id", flat=True
        )
        qs = models.Question.objects.exclude(pk__in=answered)
        count = qs.count()
        try:
            return qs[random.randint(0, count - 1)]  # nosec
        except ValueError:
            raise models.Question.DoesNotExist("No question found.")

    def get_context_data(self, **kwargs):
        qs = models.Question.objects
        total_questions = qs.count()
        answered_questions = self.participant.answer_set.count()

        context = super().get_context_data(**kwargs)
        context["name"] = self.survey.employee_name
        context["statement"] = self.question.get_display(self.survey)
        context["can_skip"] = self.survey.participant_can_skip
        context["show_question_progress"] = self.survey.show_question_progress
        context["answered_questions"] = answered_questions
        context["total_questions"] = total_questions
        return context

    def get_initial(self):
        initial = super().get_initial()
        if self.request.method == "GET":
            initial["question"] = self.question.pk
        return initial

    def form_valid(self, form):
        if form.data["undo"] == "true":
            try:
                latest_answer = models.Answer.objects.filter(
                    participant=self.participant
                ).latest("created")
                kwargs = {
                    "survey_pk": self.survey.pk,
                    "token": self.token,
                    "question_pk": latest_answer.question.pk,
                }
                latest_answer.delete()
                return HttpResponseRedirect(
                    reverse("surver-answer-specific", kwargs=kwargs)
                )
            except models.Answer.DoesNotExist:
                return self.redirect_survey_answer(self.survey.pk, self.token)
        elif (
            form.cleaned_data["decision"] is not None
            or self.survey.participant_can_skip
        ):
            self.object = form.save(commit=False)
            self.object.participant = self.participant
            self.object.survey = self.survey
            self.object.save()
            return HttpResponseRedirect(self.request.path)
        else:
            return HttpResponseForbidden()

    def redirect_survey_answer(self, survey_pk, token):
        kwargs = {
            "survey_pk": survey_pk,
            "token": self.token,
        }
        return HttpResponseRedirect(reverse("survey-answer", kwargs=kwargs))
