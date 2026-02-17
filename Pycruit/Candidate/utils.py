import random
from .models import Question

SECTIONS = {
    "Frontend": 2,
    "Backend": 2,
    "Full Stack": 2,
    "IT Support": 2,
    "Aptitude": 2
}

def generate_randomized_questions():
    section_questions = []

    for domain, count in SECTIONS.items():
        qs = list(Question.objects.filter(domain__name=domain))
        selected = random.sample(qs, count)
        section_questions.append([q.id for q in selected])

    return section_questions
