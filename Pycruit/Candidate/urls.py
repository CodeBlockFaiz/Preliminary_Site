from django.urls import path
from . import views
from .views import start_interview, get_section_questions, submit_interview,report_violation ,upload_question_file, start_skill_assessment
urlpatterns = [
    path("start/", start_interview),
    path("section/", get_section_questions),
    path("submit/", submit_interview),
    path("violation/", report_violation),
    path('upload/', views.upload_question_file),
    path('startassessment/skill/<str:skill>/', views.start_skill_assessment),
    path('login/', views.login_view),
    path('userdetails/', views.user_details),

    path('startassessment/skill/fullstack/', views.start_fullstack),
    path('startassessment/psychometric/', views.start_psychometric),

    path('userscore/', views.user_score),

    path('manager/dashboard/', views.manager_dashboard),
    path('manager/export/', views.export_candidates),

]
