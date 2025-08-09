from rest_framework import generics
from core.permissions import IsAdminUser
from .models import Worker
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import *
from django.db.models import Q


class WorkerCreateView(generics.CreateAPIView):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer
    permission_classes = [IsAdminUser]


class WorkerRetrieveView(generics.RetrieveAPIView):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'uid'


class WorkerUpdateView(generics.UpdateAPIView):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'uid'


class WorkerDeleteView(generics.DestroyAPIView):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'uid'


class WorkerListView(generics.ListAPIView):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer
    permission_classes = [IsAdminUser]


# class WorkerSalaryPaymentView(generics.UpdateAPIView):
#     queryset = Worker.objects.all()
#     serializer_class = WorkerSalaryPaymentSerializer
#     permission_classes = [IsAdminUser]
#     lookup_field = 'uid'
#
#     def update(self, request, *args, **kwargs):
#         worker = self.get_object()
#         serializer = self.get_serializer(worker, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response({
#             "worker": f"{worker.name} {worker.last_name}",
#             "total_salary": worker.salary,
#             "paid_salary": worker.paid_salary,
#             "remaining_salary": worker.salary - worker.paid_salary
#         }, status=status.HTTP_200_OK)


class WorkerSearchAPIView(generics.ListAPIView):
    serializer_class = WorkerSerializer

    def get_queryset(self):
        queryset = Worker.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(
                Q(name__icontains=name) | Q(last_name__icontains=name)
            )
        return queryset