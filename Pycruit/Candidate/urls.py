from django.urls import path
from .views import start_interview, get_section_questions, submit_interview,report_violation

urlpatterns = [
    path("start/", start_interview),
    path("section/", get_section_questions),
    path("submit/", submit_interview),
    path("violation/", report_violation),

]
