from django.urls import path
from .views import candidate_login

urlpatterns = [
    path('login/', candidate_login),
]

