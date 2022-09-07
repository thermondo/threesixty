import json

from django.core import mail, signing
from django.urls import reverse

from threesixty.models import Answer, Participant, Question, Survey


class TestViews:
    def create_survey(self):
        survey = Survey(
            employee_name="sebastian",
            employee_gender="male",
            employee_email="sebastian@mail.com",
            manager_email="johannes@mail.com",
        )
        return survey

    def create_participant(self, survey_pk):
        participant = Participant(
            email="sebastian@mail.com",
            survey_id=survey_pk,
            relation="self",
        )
        return participant

    def create_question(self):
        question = Question(
            text="how good is he?",
            attribute="porfessionalitaet",
            connotation=True,
        )
        return question

    def create_answer(self, question, survey, participant, **kwargs):
        answer = Answer(
            survey=survey,
            question=question,
            participant=participant,
            **kwargs,
        )
        return answer


class TestSurveyDetailView(TestViews):
    def test_get_survey(self, client, db):
        survey = self.create_survey()
        survey.save()
        response = client.get(survey.get_absolute_url())

        assert response.status_code == 200
        assert response.context["object"].employee_name == "sebastian"
        assert response.context["object"].participant_can_skip is False

    def test_get_survey_can_skip(self, db, client):
        survey = self.create_survey()
        survey.participant_can_skip = True
        survey.save()

        response = client.get(survey.get_absolute_url())

        assert response.status_code == 200
        assert response.context["object"].employee_name == "sebastian"
        assert response.context["object"].participant_can_skip is True

    def test_get_survey_show_question_progress(self, db, client):
        survey = self.create_survey()
        survey.show_question_progress = True
        survey.save()

        response = client.get(survey.get_absolute_url())

        assert response.status_code == 200
        assert response.context["object"].employee_name == "sebastian"
        assert response.context["object"].show_question_progress is True


class TestSurveyUpdateView(TestViews):
    def test_get_update_view(self, client, db):
        survey = self.create_survey()
        survey.is_complete = True
        survey.save()

        response = client.get(survey.get_absolute_url())

        assert response.status_code == 200
        assert response.context["widget"]["attrs"]["checked"]

    def test_set_is_complete_true(self, client, db):
        survey = self.create_survey()
        survey.is_complete = False
        survey.save()

        client.post(survey.get_absolute_url(), {"is_complete": "True"})

        assert Survey.objects.get().is_complete

    def test_set_is_complete_false(self, client, db):
        survey = self.create_survey()
        survey.is_complete = True
        survey.save()

        client.post(survey.get_absolute_url(), {"is_complete": "False"})

        assert not Survey.objects.get().is_complete


class TestSurveyDataView(TestViews):
    def create_questions(self):
        questions = []
        for i in range(1, 4):
            question = Question(
                text="Question %s" % i,
                attribute="attribute %s" % i,
                connotation=True,
            )
            question.save()
            questions.append(question)
        for i in range(4, 7):
            question = Question(
                text="Question %s" % i,
                attribute="attribute %d" % (i - 3),
                connotation=False,
            )
            question.save()
            questions.append(question)
        return questions

    def create_answer(self, name, relation, questions, survey, modulo):
        participant = Participant(
            email="%s@mail.com" % name,
            survey_id=survey.pk,
            relation=relation,
        )
        participant.save()
        for i in range(6):
            answer = Answer(
                survey=survey,
                question=questions[i],
                decision=i % modulo == 0,
                participant=participant,
            )
            answer.save()

    def create_survey_answer_test_data(self):
        questions = self.create_questions()
        survey = self.create_survey()
        survey.is_complete = True
        survey.save()

        self.create_answer(
            name="peter",
            relation="peer",
            questions=questions,
            survey=survey,
            modulo=4,
        )
        self.create_answer(
            name="george",
            relation="subordinate",
            questions=questions,
            survey=survey,
            modulo=2,
        )
        self.create_answer(
            name="sebastian",
            relation="self",
            questions=questions,
            survey=survey,
            modulo=3,
        )

        return survey

    def test_data_view_values(self, db, client):
        survey = self.create_survey_answer_test_data()

        url = reverse(
            "survey-data",
            kwargs={"pk": survey.pk, "token": survey.get_token(survey.manager_email)},
        )

        response = client.get(url)

        data = json.loads(response.content)["datasets"]
        labels = json.loads(response.content)["labels"]

        results_by_label = {result["label"]: result for result in data}

        result_peer = results_by_label["peer"]
        result_subordinate = results_by_label["subordinate"]
        result_self = results_by_label["self"]
        result_total = results_by_label["total"]
        result_benchmark = results_by_label["benchmark"]

        assert result_peer["label"] == "peer"
        result_peer_data = self.group_data_labels(labels, result_peer["data"])
        assert result_peer_data["attribute 1"] == 1.0
        assert result_peer_data["attribute 2"] == 0
        assert result_peer_data["attribute 3"] == 0.5

        assert result_subordinate["label"] == "subordinate"
        result_subordinate_data = self.group_data_labels(
            labels, result_subordinate["data"]
        )
        assert result_subordinate_data["attribute 1"] == 1.0
        assert result_subordinate_data["attribute 2"] == 0.0
        assert result_subordinate_data["attribute 3"] == 1.0

        assert result_self["label"] == "self"
        result_self_data = self.group_data_labels(labels, result_self["data"])
        assert result_self_data["attribute 1"] == 0.5
        assert result_self_data["attribute 2"] == 0.5
        assert result_self_data["attribute 3"] == 0.5

        assert result_total["label"] == "total"
        result_total_data = self.group_data_labels(labels, result_total["data"])
        assert result_total_data["attribute 1"] == 1.0
        assert result_total_data["attribute 2"] == 0.0
        assert result_total_data["attribute 3"] == 0.75

        assert result_benchmark["label"] == "benchmark"
        result_benchmark_data = self.group_data_labels(labels, result_benchmark["data"])
        assert result_benchmark_data["attribute 1"] == 1.0
        assert result_benchmark_data["attribute 2"] == 0.0
        assert result_benchmark_data["attribute 3"] == 0.75

    def group_data_labels(self, labels, data_points):
        """Group labels with data.

        labels = ['a1','a2','a3']
        data_points = [0,1,2]

        result: {'a1': 0, 'a2': 1, 'a3': }
        """
        return dict(zip(labels, data_points))


class TestParticipantCreateView(TestViews):
    def test_get_form(self, client, db):
        survey = self.create_survey()
        survey.save()

        url = reverse(
            "survey-invite",
            kwargs={
                "survey_pk": survey.pk,
                "token": survey.get_token(survey.manager_email),
            },
        )
        response = client.get(url)

        assert response.status_code == 200

    def test_send_invite(self, client, db):
        survey = self.create_survey()
        survey.save()

        url = reverse(
            "survey-invite",
            kwargs={
                "survey_pk": survey.pk,
                "token": survey.get_token(survey.manager_email),
            },
        )
        response = client.post(url, {"email": "peter@mail.com", "relation": "peer"})

        assert response.status_code == 302
        assert mail.outbox[0].recipients()[0] == "peter@mail.com"
        assert Participant.objects.get().email == "peter@mail.com"


class TestSurveyCreateView(TestViews):
    def test_create_survey(self, client, db):
        response = client.post(
            "/create",
            {
                "employee_name": "sebastian",
                "employee_email": "sebastian@mail.com",
                "employee_gender": "male",
                "manager_email": "joe@mail.com",
                "participant_can_skip": "False",
                "show_question_progress": "False",
            },
        )

        assert response.status_code == 302
        assert "joe@mail.com" in response.url

        assert mail.outbox[0].recipients()[0] == "joe@mail.com"
        assert mail.outbox[1].recipients()[0] == "sebastian@mail.com"

        assert len(Survey.objects.all()) == 1


class TestAnswerCreateView(TestViews):
    def test_get_when_no_question(self, client, db):
        survey = self.create_survey()
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        response = client.get(participant.get_absolute_url())

        assert response.status_code == 302
        assert response.url == "/thanks"

    def test_get_one_question_left(self, client, db):
        survey = self.create_survey()
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        question = self.create_question()
        question.save()

        response = client.get(participant.get_absolute_url())

        assert response.status_code == 200
        assert response.context["name"] == survey.employee_name
        assert response.context["statement"] == question.text
        assert response.context["answered_questions"] == 0
        assert response.context["total_questions"] == 1

    def test_form_valid_skip_not_allowed_skip(self, client, db):
        survey = self.create_survey()
        survey.participant_can_skip = False
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        question = self.create_question()
        question.save()

        response = client.post(
            participant.get_absolute_url(),
            {"decision": 1, "question": question.pk, "undo": "false"},
        )

        assert response.status_code == 403

    def test_form_valid_skip_allowed(self, client, db):
        survey = self.create_survey()
        survey.participant_can_skip = True
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        question = self.create_question()
        question.save()

        response = client.post(
            participant.get_absolute_url(),
            {"decision": 1, "question": question.pk, "undo": "false"},
        )

        assert response.status_code == 302  # since no more questions are left

    def test_question_answered(self, client, db):
        survey = self.create_survey()
        survey.participant_can_skip = False
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        question1 = self.create_question()
        question1.save()
        question2 = Question(
            text="how goodst is he?",
            attribute="porfessionalitaet",
            connotation=True,
        )
        question2.save()

        answer = self.create_answer(question1, survey, participant)
        answer.save()

        response = client.get(participant.get_absolute_url())

        assert response.status_code == 200
        assert response.context["name"] == survey.employee_name
        assert response.context["statement"] == question2.text
        assert response.context["answered_questions"] == 1
        assert response.context["total_questions"] == 2

    def test_get_specific_question(self, client, db):
        survey = self.create_survey()
        survey.participant_can_skip = True
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        question = self.create_question()
        question.save()

        question1 = Question(
            text="h0w good is hes?",
            attribute="porfessionalitaet",
            connotation=True,
        )
        question1.save()

        signer = signing.TimestampSigner()
        token = signer.sign(participant.email)

        kwargs = {"survey_pk": survey.pk, "token": token, "question_pk": question.pk}

        response = client.get(reverse("surver-answer-specific", kwargs=kwargs))

        assert response.context[0]["statement"] == question.text

    def test_undo(self, client, db):
        survey = self.create_survey()
        survey.participant_can_skip = True
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        question = self.create_question()
        question.save()

        question1 = Question(
            text="h0w good is hes?",
            attribute="porfessionalitaet",
            connotation=True,
        )
        question1.save()

        answer = Answer(survey=survey, question=question, participant=participant)
        answer.save()

        answer1 = Answer(survey=survey, question=question1, participant=participant)
        answer1.save()

        response = client.post(
            participant.get_absolute_url(),
            {"decision": "", "question": question.pk, "undo": "true"},
        )

        assert response.status_code == 302
        assert Answer.objects.count() == 1
        assert Answer.objects.get().pk == answer.pk
        assert Answer.objects.get().question == question
        assert Answer.objects.get().decision is None

    def test_submit_answer_yes(self, client, db):
        survey = self.create_survey()
        survey.participant_can_skip = True
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        question = self.create_question()
        question.save()

        response = client.post(
            participant.get_absolute_url(),
            {"decision": 2, "question": question.pk, "undo": "false"},
        )

        assert response.status_code == 302
        assert Answer.objects.count() == 1
        assert Answer.objects.last().decision

    def test_submit_answer_no(self, client, db):
        survey = self.create_survey()
        survey.participant_can_skip = True
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        question = self.create_question()
        question.save()

        response = client.post(
            participant.get_absolute_url(),
            {"decision": 3, "question": question.pk, "undo": "false"},
        )

        assert response.status_code == 302
        assert Answer.objects.count() == 1
        assert not Answer.objects.last().decision

    def test_undo_with_no_skip(self, client, db):
        survey = self.create_survey()
        survey.participant_can_skip = False
        survey.save()
        participant = self.create_participant(survey.pk)
        participant.save()
        question = self.create_question()
        question.save()

        question1 = Question(
            text="h0w good is hes?",
            attribute="porfessionalitaet",
            connotation=True,
        )
        question1.save()

        answer = Answer(survey=survey, question=question, participant=participant)
        answer.save()

        answer1 = Answer(survey=survey, question=question1, participant=participant)
        answer1.save()

        response = client.post(
            participant.get_absolute_url(),
            {"decision": "", "question": question.pk, "undo": "true"},
        )

        assert response.status_code == 302
        assert Answer.objects.count() == 1
        assert Answer.objects.get().pk == answer.pk
        assert Answer.objects.get().question == question
        assert Answer.objects.get().decision is None
