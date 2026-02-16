from django.shortcuts import render
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def candidate_login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if user and user.role == "candidate":
        login(request, user)
        return Response({"message": "Login successful"})
    
    return Response({"error": "Invalid credentials"}, status=401)
