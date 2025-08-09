# urls.py
from django.urls import path
from .views import *

urlpatterns = [

    path('barns/', BarnListView.as_view()),
    path('barns_list/create/', BarnCreateView.as_view()),
    path('barns/<uuid:uid>/', BarnRetrieveView.as_view()),
    path('barns/<uuid:uid>/update/', BarnUpdateView.as_view()),
    path('barns/<uuid:uid>/delete/', BarnDeleteView.as_view()),
    path('barns_search/', BarnSearchAPIView.as_view()),



]