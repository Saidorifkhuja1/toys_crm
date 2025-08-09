from django.urls import path
from .views import *

urlpatterns = [
    path('workers/', WorkerListView.as_view()),
    path('workers_create/', WorkerCreateView.as_view()),
    path('workers_details/<uuid:uid>/', WorkerRetrieveView.as_view()),
    path('workers/<uuid:uid>/update/', WorkerUpdateView.as_view()),
    path('workers/<uuid:uid>/delete/', WorkerDeleteView.as_view()),
    # path('workers/<uuid:uid>/pay-salary/', WorkerSalaryPaymentView.as_view()),
    path('workers_search/', WorkerSearchAPIView.as_view()),


]


