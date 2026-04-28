from django.db import models

from care.utils.models.base import BaseModel


class PGRComplaints(BaseModel):
    class WorkflowTypes(models.TextChoices):
        SYSTEM = "system"
        HEALTHSERVICE = "healthservice"

    class PGRStatusTypes(models.TextChoices):
        PENDING_SYNC = "pending_sync"
        SYNCED = "synced"
        ASSIGNED = "assigned"
        IN_PROGRESS = "in_progress"
        RESOLVED = "resolved"
        REJECTED = "rejected"
        CLOSED = "closed"
        SYNC_FAILED = "sync_failed"


    reporter = models.UUIDField(
        null=False,
        blank=False,
        help_text="UUID of the reporter (users_user.external_id or emr_patient.external_id)"
    )

    reporter_type = models.CharField(
        max_length=20,
        choices=[
            ("staff", "Staff"),
            ("patient", "Patient"),
        ],
        null=False,
        blank=False
    )


    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.CASCADE,
        null=False
    )
    app_context = models.JSONField(
        default=dict,
        blank=True
    )
    service_code = models.CharField(
        max_length=100,
        null=False,
        blank=False
    )
    workflow = models.CharField(
        max_length=50,
        choices=WorkflowTypes.choices,
        null=False,
        blank=False
    )

    pgr_ticket_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=False
    )

    pgr_status = models.CharField(
        max_length=50,
        choices=PGRStatusTypes.choices,
        null=True,
        blank=False
    )

    pgr_last_synced_at = models.DateTimeField(null=True, blank=True)
    pgr_response = models.JSONField(null=True, blank=True)
    last_sync_error = models.TextField(null=True, blank=True)


    class Meta:
        db_table = "pgr_complaints"
        verbose_name = "PGR Complaints"

        indexes = [
            models.Index(fields=["facility", "pgr_status"]),
            models.Index(fields=["facility", "pgr_status", "pgr_last_synced_at"])
        ]

    def __str__(self):
        return f"{self.pgr_ticket_id} ({self.pgr_status})"
