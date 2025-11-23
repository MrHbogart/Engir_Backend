import secrets
import string
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


def generate_class_code(length: int = 6) -> str:
    """Return an easy-to-share class code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Teacher(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='teacher_profile', null=True, blank=True
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    headline = models.CharField(max_length=180, blank=True)
    bio = models.TextField(blank=True)
    profile_url = models.URLField(blank=True)
    avatar_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self) -> str:
        return self.full_name

    def save(self, *args, **kwargs):
        if self.user and not self.full_name:
            self.full_name = self.user.get_full_name() or self.user.username
        if self.user and not self.email:
            self.email = self.user.email
        super().save(*args, **kwargs)


class Student(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    interests = models.JSONField(default=list, blank=True)
    timezone = models.CharField(max_length=64, blank=True)
    avatar_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self) -> str:
        return self.full_name


class Classroom(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='classes')
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=8, unique=True, editable=False)
    starts_at = models.DateTimeField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=45)
    capacity = models.PositiveIntegerField(default=12)
    meeting_url = models.URLField(blank=True)
    tags = models.JSONField(default=list, blank=True, help_text='Array of short labels displayed on cards')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.title} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_unique_code()
        super().save(*args, **kwargs)

    def _generate_unique_code(self) -> str:
        code = generate_class_code()
        while Classroom.objects.filter(code=code).exists():
            code = generate_class_code()
        return code

    @property
    def confirmed_enrollments(self) -> int:
        return self.enrollments.filter(status__in=[Enrollment.Status.PENDING, Enrollment.Status.CONFIRMED]).count()

    @property
    def available_seats(self) -> int:
        remaining = self.capacity - self.confirmed_enrollments
        return remaining if remaining > 0 else 0

    @property
    def is_full(self) -> bool:
        return self.available_seats == 0

    @property
    def next_session(self):
        return (
            self.sessions.filter(status__in=[Session.Status.SCHEDULED, Session.Status.LIVE])
            .order_by('starts_at')
            .first()
        )


class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(
        'Student', on_delete=models.SET_NULL, related_name='enrollments', null=True, blank=True
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone_number = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    source = models.CharField(max_length=50, blank=True, help_text='Optional tracking tag such as landing page or referral code')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['classroom', 'email'], name='unique_enrollment_per_email'),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} → {self.classroom.title}"


class Session(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        LIVE = 'live', 'Live'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    class StreamProvider(models.TextChoices):
        CUSTOM = 'custom', 'Custom RTMP'
        ZOOM = 'zoom', 'Zoom'
        GOOGLE_MEET = 'google_meet', 'Google Meet'
        YOUTUBE = 'youtube', 'YouTube Live'
        OTHER = 'other', 'Other'

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=45)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    stream_provider = models.CharField(
        max_length=20, choices=StreamProvider.choices, default=StreamProvider.CUSTOM
    )
    stream_key = models.CharField(max_length=64, blank=True)
    host_url = models.URLField(blank=True)
    playback_url = models.URLField(blank=True)
    recording_url = models.URLField(blank=True)
    meeting_passcode = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['starts_at']

    def __str__(self) -> str:
        return f"{self.classroom.title} — {self.title} ({self.status})"

    def save(self, *args, **kwargs):
        if self.starts_at and not self.ends_at:
            self.ends_at = self.starts_at + timedelta(minutes=self.duration_minutes)
        if self.stream_provider == self.StreamProvider.CUSTOM and not self.stream_key:
            self.stream_key = self._generate_stream_key()
        if self.stream_key:
            base = 'https://live.engir.app'
            self.host_url = self.host_url or f'{base}/host/{self.stream_key}'
            self.playback_url = self.playback_url or f'{base}/watch/{self.stream_key}'
        super().save(*args, **kwargs)

    def _generate_stream_key(self) -> str:
        token = secrets.token_urlsafe(16)
        return token.replace('-', '').upper()

    def regenerate_stream_credentials(self):
        self.stream_key = self._generate_stream_key()
        self.host_url = ''
        self.playback_url = ''
        self.save(update_fields=['stream_key', 'host_url', 'playback_url', 'updated_at'])
        return self.stream_key

    def mark_live(self):
        self.status = self.Status.LIVE
        self.save(update_fields=['status', 'updated_at'])

    def mark_completed(self, recording_url: Optional[str] = None):
        self.status = self.Status.COMPLETED
        if recording_url:
            self.recording_url = recording_url
        self.save(update_fields=['status', 'recording_url', 'updated_at'])

    @property
    def is_joinable(self) -> bool:
        return self.status in {self.Status.SCHEDULED, self.Status.LIVE}

    @property
    def is_live(self) -> bool:
        if self.status != self.Status.LIVE:
            return False
        if not self.ends_at:
            return True
        return timezone.now() <= self.ends_at + timedelta(minutes=5)

    @property
    def has_recording(self) -> bool:
        return bool(self.recording_url)
