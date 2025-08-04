from django.shortcuts import render
from core.permissions import IsAdminUser
from .models import Barn
from .serializers import BarnSerializer
from rest_framework import generics

class BarnCreateView(generics.CreateAPIView):
    queryset = Barn.objects.all()
    serializer_class = BarnSerializer
    permission_classes = [ IsAdminUser]


class BarnRetrieveView(generics.RetrieveAPIView):
    queryset = Barn.objects.all()
    serializer_class = BarnSerializer
    permission_classes = [ IsAdminUser]
    lookup_field = 'uid'


class BarnUpdateView(generics.UpdateAPIView):
    queryset = Barn.objects.all()
    serializer_class = BarnSerializer
    permission_classes = [ IsAdminUser]
    lookup_field = 'uid'


class BarnDeleteView(generics.DestroyAPIView):
    queryset = Barn.objects.all()
    serializer_class = BarnSerializer
    permission_classes = [ IsAdminUser]
    lookup_field = 'uid'


class BarnListView(generics.ListAPIView):
    queryset = Barn.objects.all()
    serializer_class = BarnSerializer