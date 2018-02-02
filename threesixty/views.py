import random

from django.core import signing
from django.core.mail import send_mail
from django.db.models import Avg, FloatField, IntegerField
from django.db.models.functions import Cast
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import generic

from . import forms
from . import models


class WithEmailTokenMixin:
    def dispatch(self, request, *args, **kwargs):
        self.token = kwargs['token']
        signer = signing.TimestampSigner()
        try:
            self.email = signer.unsign(self.token)
        except signing.BadSignature:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['token'] = self.token
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
            survey_pk = self.kwargs['survey_pk']
        except KeyError:
            raise Http404
        return get_object_or_404(models.Survey, pk=survey_pk)


class SurveyDetailView(EmployeeRequiredMixin, generic.DetailView):
    model = models.Survey


class ParticipantCreateView(EmployeeRequiredMixin, SurveyViewMixin, generic.CreateView):
    model = models.Participant
    fields = (
        'email',
        'relation',
    )

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.survey = self.survey
        self.object.save()
        self.send_invite()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('survey-view', kwargs={'pk': self.survey.pk, 'token': self.token})

    def send_invite(self):
        context = {
            'employee_name': self.survey.employee_name,
            'survey_url': self.request.build_absolute_uri(self.object.get_absolute_url()),
        }
        subject = "360-degree feedback - %s" % self.survey.employee_name
        msg = render_to_string('threesixty/invite_email.txt', context)
        send_mail(
            subject=subject,
            message=msg,
            from_email=self.survey.manager_email,
            recipient_list=[self.object.email]
        )


class SurveyCreateView(generic.CreateView):
    model = models.Survey
    fields = '__all__'

    def form_valid(self, form):
        response = super().form_valid(form=form)
        self.send_manager_mail()
        self.send_employee_mail()
        return response

    def send_manager_mail(self):
        context = {
            'employee_name': self.object.employee_name,
            'survey_url': self.request.build_absolute_uri(self.object.get_manager_url()),
        }
        subject = "360-degree feedback - %s" % self.object.employee_name
        msg = render_to_string('threesixty/manager_email.txt', context)
        send_mail(
            subject=subject,
            message=msg,
            from_email=self.object.manager_email,
            recipient_list=[self.object.manager_email]
        )

    def send_employee_mail(self):
        context = {
            'employee_name': self.object.employee_name,
            'survey_url': self.request.build_absolute_uri(self.object.get_employee_url()),
        }
        subject = "360-degree feedback"
        msg = render_to_string('threesixty/employee_email.txt', context)
        send_mail(
            subject=subject,
            message=msg,
            from_email=self.object.manager_email,
            recipient_list=[self.object.employee_email]
        )


class AnswerCreateView(WithEmailTokenMixin, SurveyViewMixin, generic.CreateView):
    model = models.Answer
    form_class = forms.AnswerForm

    def post(self, request, *args, **kwargs):
        self.participant = get_object_or_404(models.Participant, email=self.email, survey=self.survey)
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.participant = get_object_or_404(models.Participant, email=self.email, survey=self.survey)
        try:
            self.question = self.get_question()
        except models.Question.DoesNotExist:
            return HttpResponseRedirect(reverse('thanks'))
        else:
            return super().get(request, *args, **kwargs)

    def get_question(self):
        answered = self.participant.answer_set.all().values_list('question_id', flat=True)
        qs = models.Question.objects.exclude(pk__in=answered)
        count = qs.count()
        try:
            return qs[random.randint(0, count - 1)]
        except ValueError:
            raise models.Question.DoesNotExist('No question found.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['name'] = self.survey.employee_name
        context['statement'] = self.question.get_display(self.survey)
        return context

    def get_initial(self):
        initial = super().get_initial()
        if self.request.method == 'GET':
            initial['question'] = self.question.pk
        return initial

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.participant = self.participant
        self.object.survey = self.survey
        self.object.save()
        return HttpResponseRedirect(self.request.path)
