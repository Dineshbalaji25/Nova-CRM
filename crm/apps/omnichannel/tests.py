from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.omnichannel.models import SupportChatMessage
from apps.users.models import Organization, OrganizationMember


class SupportChatMessageViewSetTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.organization = Organization.objects.create(name='Acme', slug='acme')
        self.user = self.user_model.objects.create_user(email='user@example.com', password='testpass123')
        OrganizationMember.objects.create(
            organization=self.organization,
            user=self.user,
            role='member',
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_TENANT_ID=str(self.organization.id))
        self.endpoint = '/api/v1/omnichannel/support-chat/'

    def test_create_support_chat_message_sets_expected_defaults(self):
        response = self.client.post(self.endpoint, {'message': 'Need help with setup'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        message = SupportChatMessage.objects.get(id=response.data['id'])
        self.assertEqual(message.user, self.user)
        self.assertEqual(message.tenant_id, self.organization.id)
        self.assertFalse(message.is_from_support)
        self.assertEqual(message.message, 'Need help with setup')

    def test_polling_returns_user_and_support_messages_in_order(self):
        self.client.post(self.endpoint, {'message': 'Hello support'}, format='json')
        SupportChatMessage.objects.create(
            tenant=self.organization,
            user=self.user,
            is_from_support=True,
            message='Hi! How can we assist you?',
        )

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['message'], 'Hello support')
        self.assertFalse(response.data['results'][0]['is_from_support'])
        self.assertEqual(response.data['results'][1]['message'], 'Hi! How can we assist you?')
        self.assertTrue(response.data['results'][1]['is_from_support'])
