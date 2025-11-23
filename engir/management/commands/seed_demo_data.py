from datetime import timedelta
from random import choice

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from engir.models import Classroom, Enrollment, Session, Student, Teacher


class Command(BaseCommand):
    help = 'Seed the database with demo teachers, students, classrooms, and sessions.'

    def handle(self, *args, **options):
        User = get_user_model()
        teacher_user, _ = User.objects.get_or_create(
            username='mentor@engir.demo',
            defaults={'email': 'mentor@engir.demo', 'first_name': 'Demo', 'last_name': 'Mentor'},
        )
        if not teacher_user.has_usable_password():
            teacher_user.set_password('demo-classroom')
            teacher_user.save()

        teacher, _ = Teacher.objects.get_or_create(
            user=teacher_user,
            defaults={
                'full_name': 'Demo Mentor',
                'email': teacher_user.email,
                'headline': 'Teaching livestreams 101',
                'bio': 'I help educators launch engaging, community-first livestream classrooms.',
            },
        )

        student_users = []
        for idx in range(1, 4):
            email = f'student{idx}@engir.demo'
            user, _ = User.objects.get_or_create(
                username=email,
                defaults={'email': email, 'first_name': f'Student {idx}', 'last_name': 'Demo'},
            )
            if not user.has_usable_password():
                user.set_password('demo-classroom')
                user.save()
            student, _ = Student.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f'Demo Student {idx}',
                    'email': email,
                    'bio': 'Curious learner exploring remote classrooms.',
                    'timezone': 'UTC',
                },
            )
            student_users.append(student)

        classrooms = []
        for name in ['Streaming Basics', 'Camera Presence Workshop', 'Community Q&A']:
            classroom, _ = Classroom.objects.get_or_create(
                teacher=teacher,
                title=name,
                defaults={
                    'description': f'{name} powered by Engir demo data.',
                    'duration_minutes': 60,
                    'capacity': 20,
                    'tags': ['demo', 'engir'],
                },
            )
            classrooms.append(classroom)

        now = timezone.now()
        for idx, classroom in enumerate(classrooms, start=1):
            session, _ = Session.objects.get_or_create(
                classroom=classroom,
                title=f'{classroom.title} Session {idx}',
                starts_at=now + timedelta(days=idx),
                defaults={'description': 'Hands-on collaborative stream.'},
            )
            for student in student_users:
                Enrollment.objects.get_or_create(
                    classroom=classroom,
                    student=student,
                    defaults={
                        'full_name': student.full_name,
                        'email': student.email,
                        'status': choice(list(Enrollment.Status.values)),
                    },
                )

        self.stdout.write(self.style.SUCCESS('Demo data ready. Use mentor@engir.demo / demo-classroom to log in.'))
