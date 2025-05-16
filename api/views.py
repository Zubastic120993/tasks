from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Category, Task
from .serializers import CategorySerializer, TaskSerializer
from .permissions import IsOwner
from django_filters.rest_framework import DjangoFilterBackend
# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

    def get_queryset(self):
        """
        This view should return a list of all categories
        for the currently authenticated user.
        """
        return self.queryset.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [ 'category','owner']

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)