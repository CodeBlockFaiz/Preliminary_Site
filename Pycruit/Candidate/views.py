from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import timedelta
from .models import CandidateProfile, InterviewSession, Question
from .utils import generate_randomized_questions
from django.http import HttpResponse
import random
import PyPDF2
from docx import Document

#  CONFIG
SECTION_DURATION = timedelta(minutes=10)
MAX_VIOLATIONS = 3

@api_view(['GET'])
def home(request):
    return Response({"message": "hello server started"})

# Login Endpoint (No Authentication)
@api_view(['POST'])
def login_view(request):
    role = request.data.get("role")  # user or manager
    email = request.data.get("email")
    password = request.data.get("password")

    if role not in ["user", "manager"]:
        return Response({"error": "Invalid role"}, status=400)

    return Response({
        "message": f"{role} login successful",
        "role": role
    })

# Save Candidate Details (No Authentication)
@api_view(['POST'])
def user_details(request):
    name = request.data.get("name")
    email = request.data.get("email")
    department = request.data.get("department")

    profile = CandidateProfile.objects.create(
        name=name,
        email=email,
        department=department
    )

    return Response({"message": "User details saved"})


# START INTERVIEW (No Authentication)
@api_view(['POST'])
def start_interview(request):
    email = request.data.get("email")

    if not email:
        return Response({"error": "Email is required"}, status=400)

    # Prevent re-attempt
    if InterviewSession.objects.filter(candidate_email=email, completed=True).exists():
        return Response({"error": "Interview already completed"}, status=403)

    question_order = generate_randomized_questions()

    session = InterviewSession.objects.create(
        candidate_email=email,
        question_order=question_order
    )

    return Response({
        "session_id": str(session.session_id),
        "sections": question_order
    })

@api_view(['GET'])
def start_fullstack(request):
    questions = [
        "Explain REST API",
        "Difference between React and Angular",
        "What is Django ORM?",
        "Explain JWT authentication"
    ]

    return Response({
        "assessment": "fullstack",
        "questions": questions
    })

@api_view(['GET'])
def start_psychometric(request):
    questions = [
        "How do you handle stress?",
        "Describe a challenging situation you solved.",
        "Do you prefer team work or solo work?",
        "How do you handle deadlines?"
    ]

    return Response({
        "assessment": "psychometric",
        "questions": questions
    })


# Utility to extract text from uploaded resume (PDF/DOCX/TXT)
def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

    elif file.name.endswith('.docx'):
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    elif file.name.endswith('.txt'):
        return file.read().decode('utf-8')

    return ""

# Generate MCQs from resume text using simple heuristics (for demo purposes)
def generate_mcqs(text, skill):
    sentences = [s.strip() for s in text.split('.') if len(s.split()) > 6]

    generated_questions = []

    for sentence in random.sample(sentences, min(6, len(sentences))):
        words = sentence.split()
        keyword = random.choice(words)

        question = sentence.replace(keyword, "______")

        options = random.sample(words, min(4, len(words)))

        if len(options) < 4:
            continue

        correct = options[0]

        q = Question.objects.create(
            skill=skill,
            question=question,
            option_a=options[0],
            option_b=options[1],
            option_c=options[2],
            option_d=options[3],
            correct_answer="A"
        )

        generated_questions.append(q)

    return generated_questions

# Upload File and Generate Questions (No Authentication)
@api_view(['POST'])
def upload_question_file(request):
    file = request.FILES.get('file')
    skill = request.data.get('skill')

    if not file:
        return Response({"error": "No file uploaded"}, status=400)

    text = extract_text(file)
    questions = generate_mcqs(text, skill)

    return Response({
        "message": "Questions generated successfully",
        "total_questions": len(questions)
    })


#  GET SECTION QUESTIONS (10 min timer)

@api_view(['POST'])
def get_section_questions(request):
    session_id = request.data.get("session_id")
    section_index = request.data.get("section_index")

    try:
        session = InterviewSession.objects.get(session_id=session_id)
    except InterviewSession.DoesNotExist:
        return Response({"error": "Invalid session"}, status=404)

    if session.terminated:
        return Response({"error": "Interview terminated"}, status=403)

    # If switching section → reset timer
    if section_index != session.current_section:
        session.current_section = section_index
        session.section_started_at = now()
        session.save()

    #  Section Timer Validation
    if now() > session.section_started_at + SECTION_DURATION:
        return Response({"error": "Section time expired"}, status=403)

    question_ids = session.question_order[section_index]
    questions = Question.objects.filter(id__in=question_ids)

    data = []
    for q in questions:
        data.append({
            "id": q.id,
            "text": q.text,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d
            }
        })

    return Response(data)

#  START SKILL ASSESSMENT (No Authentication)
@api_view(['GET'])
def start_skill_assessment(request, skill):
    questions = Question.objects.filter(skill=skill)
    selected = random.sample(list(questions), min(4, questions.count()))

    response_data = []

    for q in selected:
        response_data.append({
            "id": q.id,
            "question": q.question,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d,
            }
        })

    return Response({
        "skill": skill,
        "questions": response_data
    })

# SUBMIT SKILL ASSESSMENT (No Authentication)
@api_view(['POST'])
def user_score(request):
    score = random.randint(60, 95)

    return Response({
        "score": score,
        "message": "Thank you for completing the assessment"
    })


#  SUBMIT INTERVIEW (95% Criteria)

@api_view(['POST'])
def submit_interview(request):
    session_id = request.data.get("session_id")
    answers = request.data.get("answers")

    try:
        session = InterviewSession.objects.get(session_id=session_id)
    except InterviewSession.DoesNotExist:
        return Response({"error": "Invalid session"}, status=404)

    if session.completed:
        return Response({"error": "Already submitted"}, status=400)

    if session.terminated:
        return Response({"error": "Interview terminated"}, status=403)

    #  Final section timer validation
    if now() > session.section_started_at + SECTION_DURATION:
        return Response({"error": "Section time expired"}, status=403)

    total = 0
    correct = 0

    for ans in answers:
        try:
            question = Question.objects.get(id=ans["question_id"])
        except Question.DoesNotExist:
            continue

        total += question.weight

        if ans["selected_option"] == question.correct_answer:
            correct += question.weight

    if total == 0:
        return Response({"error": "No valid answers submitted"}, status=400)

    percentage = (correct / total) * 100

    session.score = percentage
    session.completed = True
    session.save()

    status = "Proceed to Next Round" if percentage >= 95 else "Not Selected"

    return Response({
        "score": round(percentage, 2),
        "status": status
    })



#  REPORT VIOLATION (Fullscreen / Tab / Media)

@api_view(['POST'])
def report_violation(request):
    session_id = request.data.get("session_id")
    violation_type = request.data.get("type")

    try:
        session = InterviewSession.objects.get(session_id=session_id)
    except InterviewSession.DoesNotExist:
        return Response({"error": "Invalid session"}, status=404)

    if session.terminated:
        return Response({"error": "Interview already terminated"}, status=403)

    if violation_type == "fullscreen":
        session.fullscreen_violations += 1
    elif violation_type == "tab":
        session.tab_switch_violations += 1
    elif violation_type == "media":
        session.media_violations += 1
    else:
        return Response({"error": "Invalid violation type"}, status=400)

    session.save()

    total_violations = (
        session.fullscreen_violations +
        session.tab_switch_violations +
        session.media_violations
    )

    if total_violations >= MAX_VIOLATIONS:
        session.terminated = True
        session.completed = True
        session.score = 0
        session.save()

        return Response({
            "status": "terminated",
            "message": "Interview terminated due to multiple violations"
        }, status=403)

    return Response({
        "status": "warning",
        "remaining_attempts": MAX_VIOLATIONS - total_violations
    })

# MANAGER DASHBOARD - View all candidates and their scores (No Authentication)
from .models import CandidateProfile

@api_view(['GET'])
def manager_dashboard(request):
    users = CandidateProfile.objects.all().values()

    return Response({
        "total_candidates": users.count(),
        "data": list(users)
    })

# MANAGER DASHBOARD - Export candidate data as CSV (No Authentication)
import csv
from django.http import HttpResponse


@api_view(['GET'])
def export_candidates(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="candidates.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Department'])

    for user in CandidateProfile.objects.all():
        writer.writerow([user.name, user.email, user.department])

    return response
