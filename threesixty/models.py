from django.core import signing
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

__all__ = ("Survey", "Question", "Answer", "Participant")


class Survey(models.Model):
    employee_name = models.CharField(_("employee name"), max_length=30)
    GENDERS = (
        ("female", _("female")),
        ("male", _("male")),
        ("other", _("other")),
    )
    employee_gender = models.CharField(
        _("employee gender"), max_length=6, choices=GENDERS, default="other"
    )
    employee_email = models.EmailField(_("employee email"))
    manager_email = models.EmailField(_("manager email"))
    is_complete = models.BooleanField(
        _("is complete"),
        default=False,
        help_text=_("Will show results and reject further answers."),
    )
    participant_can_skip = models.BooleanField(
        "participant can skip",
        default=False,
        help_text=_(
            "This option allows a participant of this survey to skip single questions."
        ),
    )
    show_question_progress = models.BooleanField(
        "show question progress",
        default=False,
        help_text=_(
            "This option displays how many questions are "
            "completed out of the total amount questions."
        ),
    )
    created = models.DateTimeField(_("created"), auto_now_add=True, editable=False)

    def __str__(self):
        return self.employee_name

    def get_token(self, email):
        signer = signing.TimestampSigner()
        return signer.sign(email)

    def get_manager_url(self):
        return reverse(
            "survey-edit",
            kwargs={"pk": self.pk, "token": self.get_token(self.manager_email)},
        )

    def get_employee_url(self):
        return reverse(
            "survey-view",
            kwargs={"pk": self.pk, "token": self.get_token(self.employee_email)},
        )

    def get_absolute_url(self):
        return self.get_manager_url()


class Question(models.Model):
    text = models.CharField(_("question"), max_length=79, db_index=True, unique=True)
    attribute = models.CharField(_("attribute"), max_length=30, db_index=True)
    CONNOTATIONS = ((True, _("positive")), (False, _("negative")))
    connotation = models.BooleanField(
        _("connotation"), choices=CONNOTATIONS, default=True
    )
    created = models.DateTimeField(_("created"), auto_now_add=True, editable=False)

    class Meta:
        get_latest_by = "created"
        ordering = ("-created",)

    def __str__(self):
        return self.text

    def get_display(self, survey):
        if survey.employee_gender in ["male", "other"]:
            return self.text
        text = self.text.replace("him", "her")
        text = text.replace("his", "her")
        text = text.replace("himself", "herself")
        return text


class Answer(models.Model):
    survey = models.ForeignKey("Survey", on_delete=models.CASCADE)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    decision = models.BooleanField(_("decision"), null=True)
    participant = models.ForeignKey("Participant", on_delete=models.CASCADE)
    created = models.DateTimeField(_("created"), auto_now_add=True, editable=False)

    class Meta:
        get_latest_by = "created"
        ordering = ("-created",)
        unique_together = ("survey", "question", "participant")

    def __str__(self):
        return str(_("yes") if self.decision else _("no"))


class Participant(models.Model):
    email = models.EmailField(_("email"))
    survey = models.ForeignKey("Survey", on_delete=models.CASCADE, editable=False)
    relations = (
        ("self", _("self")),
        ("subordinate", "subordinate"),
        ("peer", _("peer")),
        ("supervisor", _("supervisor")),
    )
    relation = models.CharField(_("relation"), max_length=11, choices=relations)
    created = models.DateTimeField(_("created"), auto_now_add=True, editable=False)

    class Meta:
        unique_together = (("email", "survey"),)

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        signer = signing.TimestampSigner()
        token = signer.sign(self.email)
        return reverse(
            "survey-answer", kwargs={"survey_pk": self.survey_id, "token": token}
        )

    @property
    def survey_completed(self):
        answered = self.answer_set.all().values_list("question_id", flat=True)
        return not Question.objects.exclude(pk__in=answered).exists()
