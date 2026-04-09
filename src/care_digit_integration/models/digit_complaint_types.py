from django.contrib.postgres.fields import ArrayField
from django.db import models

from care.utils.models.base import BaseModel


class DigitComplaintTypes(BaseModel):
    class WorkflowTypes(models.TextChoices):
        SYSTEM = "system"
        HEALTHSERVICE = "healthservice"

    class StatusTypes(models.TextChoices):
        ACTIVE = "active"
        INACTIVE = "inactive"

    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.CASCADE
    )
    tenant_id = models.CharField(max_length=100)
    workflow = models.CharField(
        max_length=50,
        choices=WorkflowTypes.choices
    )
    service_codes = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=StatusTypes.choices,
        default=StatusTypes.ACTIVE
    )

    class Meta:
        db_table = "digit_complaint_types"
        verbose_name = "Digit Complaint Type"

        constraints = [
            models.UniqueConstraint(
                fields=["facility", "tenant_id", "workflow"],
                name="unique_facility_tenant_workflow"
            )
        ]

        indexes = [
            models.Index(fields=["facility", "workflow", "status"]),
        ]

    def __str__(self):
        return f"{self.workflow} - {self.status} ({self.facility_id})"
