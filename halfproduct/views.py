from rest_framework import generics
from core.permissions import IsAdminUser
from .models import HalfProduct
from .serializers import HalfProductSerializer

class HalfProductCreateView(generics.CreateAPIView):
    queryset = HalfProduct.objects.all()
    serializer_class = HalfProductSerializer
    permission_classes = [IsAdminUser]


class HalfProductRetrieveView(generics.RetrieveAPIView):
    queryset = HalfProduct.objects.all()
    serializer_class = HalfProductSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'uid'


class HalfProductUpdateView(generics.UpdateAPIView):
    queryset = HalfProduct.objects.all()
    serializer_class = HalfProductSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'uid'


class HalfProductDeleteView(generics.DestroyAPIView):
    queryset = HalfProduct.objects.all()
    serializer_class = HalfProductSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'uid'


class HalfProductListView(generics.ListAPIView):
    queryset = HalfProduct.objects.all()
    serializer_class = HalfProductSerializer
    permission_classes = [IsAdminUser]