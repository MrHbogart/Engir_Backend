from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from engir.models import Classroom, Session, Teacher


class SessionAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='teacher@example.com', email='teacher@example.com', password='strongpass'
        )
        self.client.force_authenticate(self.user)

        self.teacher = Teacher.objects.create(user=self.user, full_name='Jane Mentor', email='teacher@example.com')
        self.classroom = Classroom.objects.create(
            teacher=self.teacher,
            title='Intro to Streaming',
            description='Learn how to host live classes with Engir.',
        )

    def test_create_session_generates_rtmp_credentials(self):
        url = reverse('session-list')
        payload = {
            'classroom_id': self.classroom.id,
            'title': 'Live Q&A',
            'description': 'Ask anything about the platform.',
            'starts_at': timezone.now() + timezone.timedelta(hours=1),
            'duration_minutes': 60,
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        session_id = response.data['id']
        session = Session.objects.get(pk=session_id)
        self.assertTrue(session.stream_key)
        self.assertTrue(session.host_url)
        self.assertTrue(session.playback_url)
        self.assertEqual(session.status, Session.Status.SCHEDULED)

    def test_stream_lifecycle_actions(self):
        session = Session.objects.create(
            classroom=self.classroom,
            title='Weekly Workshop',
            description='Hands-on class',
            starts_at=timezone.now() + timezone.timedelta(hours=2),
        )

        regen_url = reverse('session-regenerate-stream-key', args=[session.id])
        response = self.client.post(regen_url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stream_key', response.data)
        new_key = response.data['stream_key']
        session.refresh_from_db()
        self.assertEqual(session.stream_key, new_key)

        start_url = reverse('session-start-stream', args=[session.id])
        response = self.client.post(start_url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, Session.Status.LIVE)

        end_url = reverse('session-end-stream', args=[session.id])
        recording = 'https://cdn.example.com/recordings/workshop.mp4'
        response = self.client.post(end_url, {'recording_url': recording})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, Session.Status.COMPLETED)
        self.assertEqual(session.recording_url, recording)
