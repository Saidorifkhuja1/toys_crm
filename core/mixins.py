from django.db import transaction
from rest_framework.exceptions import ValidationError
from products.models import ProductPayments


from products.serializers import WriteProductPaymentSerializer
from core.enums import Actions


class InventoryLoggingMixin:
    """
    Mixin to automatically log create, update, and delete actions
    for any viewset dealing with inventory models like Product or ProductBatch.
    Subclasses must define:
      - log_model: the Log model class (e.g. ProductLog, BatchLog)
      - log_fk_field: the name of the ForeignKey field on log_model
                      pointing to the instance (e.g. "product", "batch")
      - create_note_template: format string for create notes, with access to
                              {instance} and its attrs, e.g. "{instance.name} added"
      - update_note_template: format string for update notes, with
                              {instance} and {changes}
      - delete_note_template: format string for delete notes, e.g. "{instance.sku} deleted"
      - (optionally) override create_action, update_action, delete_action
    """

    log_model = None
    log_fk_field = ""
    create_action = Actions.ADD
    update_action = Actions.ADJUST
    delete_action = Actions.DELETE
    create_note_template = ""
    update_note_template = ""
    delete_note_template = ""

    @transaction.atomic
    def perform_create(self, serializer):
        super().perform_create(serializer)
        instance = serializer.instance
        note = self.create_note_template.format(instance=instance)
        self.log_model.objects.create(
            **{self.log_fk_field: instance},
            action=self.create_action,
            note=note,
            created_by=self.request.user,
        )

    @transaction.atomic
    def perform_update(self, serializer):
        # Capture old values before update
        instance = serializer.instance
        diffs = []

        for field, new_value in serializer.validated_data.items():
            old_value = getattr(instance, field, None)

            old_value_str = str(old_value)
            new_value_str = str(new_value)

            if old_value_str != new_value_str:
                if len(old_value_str) > 30:
                    old_value_str = old_value_str[:30] + "..."
                if len(new_value_str) > 30:
                    new_value_str = new_value_str[:30] + "..."
                diffs.append(f"{field}: {old_value_str} → {new_value_str}")

        if len(diffs) > 10:
            diffs = diffs[:10]
            diffs.append("...more changes")

        changes = "; ".join(diffs)

        # Perform the actual update
        super().perform_update(serializer)
        instance = serializer.instance

        # Compose note and log the update
        note = self.update_note_template.format(instance=instance, changes=changes)
        self.log_model.objects.create(
            **{self.log_fk_field: instance},
            action=self.update_action,
            note=note,
            created_by=self.request.user,
        )

    @transaction.atomic
    def perform_destroy(self, instance):
        note = self.delete_note_template.format(instance=instance)
        self.log_model.objects.create(
            **{self.log_fk_field: instance},
            action=self.delete_action,
            note=note,
            created_by=self.request.user,
        )
        return super().perform_destroy(instance)


class PaymentMixin:
    """
    Mixin that:
     - validates & parses payments payload
     - instantiates ProductPayments (unsaved)
     - returns (payment_instances, total_paid_uzs)
    """

    def collect_payments(self, payment, user):
        serializer = WriteProductPaymentSerializer(data=payment)
        serializer.is_valid(raise_exception=True)
        exchange_rate = serializer.validated_data["exchange_rate"]
        payments_data = serializer.validated_data.get("payments", [])

        instances = []
        total_paid_uzs = 0

        for p in payments_data:
            method = p["method"].lower()
            amount = p["amount"]
            if amount > 0:
                inst = ProductPayments(
                    created_by=user,
                    method=method,
                    amount=amount,
                    product_batch=self.product_batch,
                    exchange_rate=exchange_rate,
                )
                instances.append(inst)

            if method in ("card", "uzs"):
                total_paid_uzs += amount
            elif method == "usd":
                total_paid_uzs += exchange_rate * amount
            else:
                raise ValidationError("Invalid payment type provided.")

        return instances, total_paid_uzs
