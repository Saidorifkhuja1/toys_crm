from itertools import chain
from django.db.models import Value, CharField

from core.viewsets import CoreReadOnlyViewSet
from logs.serializers import UnifiedLogSerializer
from .models import ProductLog, BatchLog


class LogViewSet(CoreReadOnlyViewSet):
    serializer_class = UnifiedLogSerializer

    def get_queryset(self):
        product_logs = (
            ProductLog.objects.select_related("product")
            .all()
            .annotate(type=Value("product", output_field=CharField()))
        )
        batch_logs = (
            BatchLog.objects.select_related("batch")
            .all()
            .annotate(type=Value("batch", output_field=CharField()))
        )
        combined_logs = sorted(
            chain(product_logs, batch_logs), key=lambda x: x.created_at, reverse=True
        )
        return combined_logs
