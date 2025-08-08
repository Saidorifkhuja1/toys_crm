from django.urls import path
from .views import (
    HalfProductCreateView,
    HalfProductRetrieveView,
    HalfProductUpdateView,
    HalfProductDeleteView,
    HalfProductListView
)

urlpatterns = [
    path('halfproduct_create/', HalfProductCreateView.as_view()),
    path('halfproduct_list/', HalfProductListView.as_view()),
    path('halfproduct_details<uuid:uid>/', HalfProductRetrieveView.as_view()),
    path('halfproduct_update/<uuid:uid>/', HalfProductUpdateView.as_view()),
    path('halfproduct_delete/<uuid:uid>/', HalfProductDeleteView.as_view()),
]