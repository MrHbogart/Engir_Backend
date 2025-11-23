from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Classroom, Enrollment, Session, Student, Teacher
from .permissions import IsStudentUser, IsTeacherOwnerOrReadOnly, IsTeacherUser
from .serializers import (
    AuthTokenSerializer,
    ClassroomSerializer,
    EnrollmentSerializer,
    SessionSerializer,
    StudentRegistrationSerializer,
    StudentSerializer,
    TeacherRegistrationSerializer,
    TeacherSerializer,
    UserSerializer,
)

User = get_user_model()


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Teacher.objects.all().order_by('full_name')
    serializer_class = TeacherSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ('full_name', 'email', 'headline')


class ClassroomViewSet(viewsets.ModelViewSet):
    serializer_class = ClassroomSerializer
    permission_classes = [IsTeacherOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ('title', 'code', 'teacher__full_name')
    ordering_fields = ('starts_at', 'created_at')

    def get_queryset(self):
        queryset = Classroom.objects.select_related('teacher').prefetch_related('enrollments', 'sessions')
        teacher_id = self.request.query_params.get('teacher')
        is_public = self.request.query_params.get('is_public')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        mine = self.request.query_params.get('mine')
        queryset = queryset.order_by('-created_at')
        if mine and mine.lower() == 'true' and hasattr(self.request.user, 'teacher_profile'):
            queryset = queryset.filter(teacher=self.request.user.teacher_profile)
        return queryset

    def perform_create(self, serializer):
        teacher = getattr(self.request.user, 'teacher_profile', None)
        if not teacher:
            raise PermissionDenied('Only teachers can create classrooms.')
        serializer.save(teacher=teacher)

    def perform_update(self, serializer):
        teacher = getattr(self.request.user, 'teacher_profile', None)
        if not teacher or serializer.instance.teacher != teacher:
            raise PermissionDenied('You can only update your own classrooms.')
        serializer.save()

    @action(detail=False, methods=['get'], url_path=r'code/(?P<code>[A-Za-z0-9]+)')
    def by_code(self, request, code: str):
        classroom = Classroom.objects.filter(code=code.upper()).select_related('teacher').first()
        if not classroom:
            return Response({'detail': 'Class not found.'}, status=404)
        serializer = self.get_serializer(classroom)
        return Response(serializer.data)


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ('full_name', 'email', 'classroom__title', 'classroom__code')
    ordering_fields = ('created_at',)

    def get_queryset(self):
        queryset = Enrollment.objects.select_related('classroom', 'classroom__teacher', 'student')
        classroom_id = self.request.query_params.get('classroom')
        status_filter = self.request.query_params.get('status')
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        student = getattr(self.request.user, 'student_profile', None)
        if student:
            serializer.save(student=student, full_name=student.full_name, email=student.email)
        else:
            serializer.save()


class SessionViewSet(viewsets.ModelViewSet):
    serializer_class = SessionSerializer
    permission_classes = [IsTeacherOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ('title', 'classroom__title', 'classroom__code')
    ordering_fields = ('starts_at', 'created_at')

    def get_queryset(self):
        queryset = Session.objects.select_related('classroom', 'classroom__teacher')
        classroom_id = self.request.query_params.get('classroom')
        status_filter = self.request.query_params.get('status')
        upcoming = self.request.query_params.get('upcoming')
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if upcoming and upcoming.lower() == 'true':
            queryset = queryset.filter(starts_at__gte=timezone.now())
        return queryset.order_by('starts_at')

    def perform_create(self, serializer):
        teacher = getattr(self.request.user, 'teacher_profile', None)
        classroom = serializer.validated_data.get('classroom')
        if not teacher or classroom.teacher != teacher:
            raise PermissionDenied('You can only schedule sessions for your classrooms.')
        serializer.save()

    def perform_update(self, serializer):
        teacher = getattr(self.request.user, 'teacher_profile', None)
        if not teacher or serializer.instance.classroom.teacher != teacher:
            raise PermissionDenied('You can only edit sessions for your classrooms.')
        serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsTeacherUser])
    def regenerate_stream_key(self, request, pk=None):
        session = self.get_object()
        key = session.regenerate_stream_credentials()
        return Response(
            {
                'stream_key': key,
                'host_url': session.host_url,
                'playback_url': session.playback_url,
            }
        )

    @action(detail=True, methods=['post'], permission_classes=[IsTeacherUser])
    def start_stream(self, request, pk=None):
        session = self.get_object()
        session.mark_live()
        return Response(self.get_serializer(session).data)

    @action(detail=True, methods=['post'], permission_classes=[IsTeacherUser])
    def end_stream(self, request, pk=None):
        session = self.get_object()
        recording_url = request.data.get('recording_url')
        session.mark_completed(recording_url=recording_url)
        return Response(self.get_serializer(session).data)


class AuthTokenView(TokenObtainPairView):
    serializer_class = AuthTokenSerializer


class TeacherRegisterView(generics.CreateAPIView):
    serializer_class = TeacherRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class StudentRegisterView(generics.CreateAPIView):
    serializer_class = StudentRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class TeacherDashboardView(APIView):
    permission_classes = [IsTeacherUser]

    def get(self, request):
        teacher = request.user.teacher_profile
        classes = (
            Classroom.objects.filter(teacher=teacher)
            .prefetch_related('sessions', 'enrollments')
            .order_by('-updated_at')
        )
        upcoming_sessions = (
            Session.objects.filter(classroom__teacher=teacher, starts_at__gte=timezone.now())
            .order_by('starts_at')[:10]
        )
        recent_enrollments = (
            Enrollment.objects.filter(classroom__teacher=teacher)
            .select_related('student', 'classroom')
            .order_by('-created_at')[:10]
        )
        return Response(
            {
                'teacher': TeacherSerializer(teacher).data,
                'classes': ClassroomSerializer(classes, many=True).data,
                'upcoming_sessions': SessionSerializer(upcoming_sessions, many=True).data,
                'recent_enrollments': EnrollmentSerializer(recent_enrollments, many=True).data,
            }
        )


class StudentDashboardView(APIView):
    permission_classes = [IsStudentUser]

    def get(self, request):
        student = request.user.student_profile
        enrollments = (
            student.enrollments.select_related('classroom', 'classroom__teacher')
            .order_by('-created_at')
            .all()
        )
        upcoming_sessions = (
            Session.objects.filter(classroom__enrollments__student=student, starts_at__gte=timezone.now())
            .select_related('classroom', 'classroom__teacher')
            .order_by('starts_at')
            .distinct()
        )
        return Response(
            {
                'student': StudentSerializer(student).data,
                'enrollments': EnrollmentSerializer(enrollments, many=True).data,
                'upcoming_sessions': SessionSerializer(upcoming_sessions, many=True).data,
            }
        )
