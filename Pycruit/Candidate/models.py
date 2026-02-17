from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import now
import uuid

class CandidateProfile(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=50)  # fullstack/backend/frontend
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Domain(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Question(models.Model):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1)
    weight = models.IntegerField(default=1)


class InterviewSession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)


    candidate_email = models.EmailField()

    question_order = models.JSONField()

    current_section = models.IntegerField(default=0)
    section_started_at = models.DateTimeField(default=now)

    score = models.FloatField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    fullscreen_violations = models.IntegerField(default=0)
    tab_switch_violations = models.IntegerField(default=0)
    media_violations = models.IntegerField(default=0)

    terminated = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

