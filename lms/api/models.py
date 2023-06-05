from uuid import uuid4

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    email = models.EmailField(
        max_length=100,
        db_index=True,
        unique=True,
    )
    id = models.UUIDField(
        default=uuid4,
        editable=False,
        primary_key=True,
    )
    lastmod = models.DateField(db_index=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return str(self.email)


class Loan(models.Model):
    STATUS_LOOKUP = {
        1: 'Pending',
        2: 'Approve',
        3: 'Due',
        4: 'Paid',
    }
    STATUS = tuple(STATUS_LOOKUP.items())
    STATUS_LOOKUP_BY_VALUE = {
        value: key for key, value in STATUS_LOOKUP.items()
    }

    amount = models.PositiveIntegerField()
    customer = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
    )
    date = models.DateField()

    id = models.UUIDField(
        default=uuid4,
        editable=False,
        primary_key=True,
    )
    lastmod = models.DateField(db_index=True)
    repay_details = models.JSONField()
    status = models.PositiveSmallIntegerField(choices=STATUS)
    term = models.PositiveSmallIntegerField()

    def __str__(self):
        return str(self.id)
