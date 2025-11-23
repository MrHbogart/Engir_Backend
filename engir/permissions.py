from rest_framework import permissions


def _get_teacher_from_object(obj):
    if hasattr(obj, 'teacher'):
        return obj.teacher
    if hasattr(obj, 'classroom'):
        return getattr(obj.classroom, 'teacher', None)
    return None


class IsTeacherUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, 'teacher_profile'))


class IsStudentUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, 'student_profile'))


class IsTeacherOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, 'teacher_profile'))

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        teacher = _get_teacher_from_object(obj)
        if not teacher or not teacher.user:
            return False
        return teacher.user == request.user
