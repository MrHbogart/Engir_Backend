from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuthTokenView,
    ClassroomViewSet,
    EnrollmentViewSet,
    MeView,
    SessionViewSet,
    StudentDashboardView,
    StudentRegisterView,
    TeacherDashboardView,
    TeacherRegisterView,
    TeacherViewSet,
)

router = DefaultRouter()
router.register('teachers', TeacherViewSet)
router.register('classes', ClassroomViewSet, basename='classroom')
router.register('enrollments', EnrollmentViewSet, basename='enrollment')
router.register('sessions', SessionViewSet, basename='session')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', AuthTokenView.as_view(), name='auth-login'),
    path('auth/register/teacher/', TeacherRegisterView.as_view(), name='auth-register-teacher'),
    path('auth/register/student/', StudentRegisterView.as_view(), name='auth-register-student'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('dashboard/teacher/', TeacherDashboardView.as_view(), name='teacher-dashboard'),
    path('dashboard/student/', StudentDashboardView.as_view(), name='student-dashboard'),
]
