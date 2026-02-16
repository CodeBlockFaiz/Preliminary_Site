from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import timedelta

from .models import InterviewSession, Question
from .utils import generate_randomized_questions


#  CONFIG
SECTION_DURATION = timedelta(minutes=10)
MAX_VIOLATIONS = 3



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
