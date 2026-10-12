import uuid

from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class IdempotentCreateMixin:
    """
    Makes POST (create) safe to retry for offline clients.

    The client sends a UUID `client_id` it generated when the record was made.
    If a record with that `client_id` already exists in the user's farm, the
    existing record is returned with 200 instead of creating a duplicate.
    Requests without `client_id` behave exactly as before.
    """

    def create(self, request, *args, **kwargs):
        client_id = self._parse_client_id(request.data.get('client_id'))
        if client_id is None:
            return super().create(request, *args, **kwargs)

        existing = self._find_existing(client_id)
        if existing is not None:
            return self._replay_response(existing)

        try:
            with transaction.atomic():
                return super().create(request, *args, **kwargs)
        except IntegrityError:
            # A concurrent request with the same client_id won the race.
            existing = self._find_existing(client_id)
            if existing is None:
                raise
            return self._replay_response(existing)

    @staticmethod
    def _parse_client_id(value):
        if value in (None, ''):
            return None
        try:
            return uuid.UUID(str(value))
        except ValueError:
            raise ValidationError({'client_id': ['Must be a valid UUID.']})

    def _find_existing(self, client_id):
        model = self.get_queryset().model
        existing = model.objects.filter(client_id=client_id).first()
        if existing is None:
            return None
        if not self.get_queryset().filter(pk=existing.pk).exists():
            # The id is taken by a record outside this user's farm. Don't leak it.
            raise ValidationError({'client_id': ['This client_id is already in use.']})
        return existing

    def _replay_response(self, instance):
        serializer = self.get_read_serializer(instance)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
            headers={'Idempotent-Replayed': 'true'},
        )

    def get_read_serializer(self, instance):
        return self.get_serializer(instance)


class ClientIdSerializerMixin:
    """Lets `client_id` be set on create but never changed afterwards."""

    def validate_client_id(self, value):
        if self.instance is not None and value != self.instance.client_id:
            raise ValidationError('client_id cannot be changed.')
        return value
