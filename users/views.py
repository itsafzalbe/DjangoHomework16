from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from .models import User
from .serializers import SignUpSerializer
from rest_framework import permissions


class SignUpView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = (permissions.AllowAny, )
