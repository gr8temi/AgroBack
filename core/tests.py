import uuid
from datetime import date
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Farm, User
from finances.models import Transaction
from flocks.models import EggCollection, FeedLog, Flock, HealthLog
from reports.models import DailyReport


class IdempotentCreateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='pw', role='superuser')
        self.farm = Farm.objects.create(name='Farm', owner=self.user)
        self.user.farm = self.farm
        self.user.save()
        self.flock = Flock.objects.create(
            name='Layers', breed='ISA', initial_quantity=100, current_quantity=100,
            user=self.user, farm=self.farm, start_date=date.today(),
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def post_twice(self, url, payload):
        first = self.client.post(url, payload, format='json')
        second = self.client.post(url, payload, format='json')
        return first, second

    def test_egg_collection_retry_returns_existing(self):
        payload = {'client_id': str(uuid.uuid4()), 'flock': self.flock.id,
                   'date': '2026-10-01', 'quantity_collected': 50, 'damaged': 1}
        first, second = self.post_twice('/api/egg-collections/', payload)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second['Idempotent-Replayed'], 'true')
        self.assertEqual(first.data['id'], second.data['id'])
        self.assertEqual(EggCollection.objects.count(), 1)
        self.flock.refresh_from_db()
        self.assertEqual(self.flock.total_eggs_collected, 50)

    def test_feed_log_retry_returns_existing(self):
        payload = {'client_id': str(uuid.uuid4()), 'flock': self.flock.id, 'date': '2026-10-01',
                   'quantity_kg': '25.00', 'feed_type': 'Layer mash', 'cost': '100.00'}
        first, second = self.post_twice('/api/feed-logs/', payload)

        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(FeedLog.objects.count(), 1)

    def test_mortality_retry_reduces_count_once(self):
        payload = {'client_id': str(uuid.uuid4()), 'flock': self.flock.id, 'date': '2026-10-01',
                   'log_type': 'mortality', 'description': 'heat', 'affected_birds': 3}
        first, second = self.post_twice('/api/health-logs/', payload)

        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(HealthLog.objects.count(), 1)
        self.flock.refresh_from_db()
        self.assertEqual(self.flock.total_mortality, 3)

    def test_transaction_retry_returns_existing(self):
        payload = {'client_id': str(uuid.uuid4()), 'date': '2026-10-01', 'type': 'expense',
                   'category': 'feed', 'amount': '500.00', 'related_flock': self.flock.id}
        first, second = self.post_twice('/api/transactions/', payload)

        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(Transaction.objects.count(), 1)

    @patch('reports.views.send_push_notification')
    def test_report_retry_returns_existing_and_notifies_once(self, mock_push):
        payload = {'client_id': str(uuid.uuid4()), 'reference_date': '2026-10-01', 'answers': []}
        first, second = self.post_twice('/api/reports/submissions/', payload)

        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(second.data['client_id'], payload['client_id'])
        self.assertEqual(DailyReport.objects.count(), 1)
        self.assertEqual(mock_push.call_count, 1)

    @patch('reports.views.send_push_notification')
    def test_duplicate_report_date_returns_400(self, mock_push):
        url = '/api/reports/submissions/'
        first = self.client.post(url, {'client_id': str(uuid.uuid4()), 'reference_date': '2026-10-01',
                                       'answers': []}, format='json')
        second = self.client.post(url, {'client_id': str(uuid.uuid4()), 'reference_date': '2026-10-01',
                                        'answers': []}, format='json')

        self.assertEqual((first.status_code, second.status_code), (201, 400))
        self.assertIn('reference_date', second.data)
        self.assertEqual(DailyReport.objects.count(), 1)

    def test_without_client_id_behaves_as_before(self):
        payload = {'flock': self.flock.id, 'date': '2026-10-01', 'quantity_collected': 10}
        first, second = self.post_twice('/api/egg-collections/', payload)

        self.assertEqual((first.status_code, second.status_code), (201, 201))
        self.assertEqual(EggCollection.objects.count(), 2)

    def test_invalid_client_id_rejected(self):
        payload = {'client_id': 'not-a-uuid', 'flock': self.flock.id,
                   'date': '2026-10-01', 'quantity_collected': 10}
        response = self.client.post('/api/egg-collections/', payload, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('client_id', response.data)

    def test_client_id_from_other_farm_not_leaked(self):
        other_user = User.objects.create_user(username='other', password='pw', role='superuser')
        other_farm = Farm.objects.create(name='Other', owner=other_user)
        other_flock = Flock.objects.create(
            name='Other', breed='ISA', initial_quantity=10, current_quantity=10,
            user=other_user, farm=other_farm,
        )
        taken = uuid.uuid4()
        EggCollection.objects.create(flock=other_flock, date=date.today(),
                                     quantity_collected=5, client_id=taken)

        payload = {'client_id': str(taken), 'flock': self.flock.id,
                   'date': '2026-10-01', 'quantity_collected': 10}
        response = self.client.post('/api/egg-collections/', payload, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('id', response.data)

    def test_client_id_cannot_be_changed(self):
        log = EggCollection.objects.create(flock=self.flock, date=date.today(),
                                           quantity_collected=5, client_id=uuid.uuid4())
        response = self.client.patch(f'/api/egg-collections/{log.id}/',
                                     {'client_id': str(uuid.uuid4())}, format='json')

        self.assertEqual(response.status_code, 400)
