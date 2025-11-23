from django.contrib import admin

from .models import Classroom, Enrollment, Session, Student, Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'headline', 'user', 'created_at')
    search_fields = ('full_name', 'email', 'headline', 'user__email')
    ordering = ('full_name',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'timezone', 'user', 'created_at')
    search_fields = ('full_name', 'email', 'user__email')


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ('full_name', 'email', 'phone_number', 'status', 'created_at')
    readonly_fields = ('full_name', 'email', 'phone_number', 'created_at')


class SessionInline(admin.TabularInline):
    model = Session
    extra = 0
    fields = (
        'title',
        'starts_at',
        'status',
        'stream_provider',
        'playback_url',
    )
    readonly_fields = ('playback_url',)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'code', 'starts_at', 'capacity', 'available_seats', 'is_public')
    search_fields = ('title', 'code', 'teacher__full_name')
    list_filter = ('is_public',)
    inlines = [SessionInline, EnrollmentInline]
    readonly_fields = ('code', 'created_at', 'updated_at')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'classroom', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('full_name', 'email', 'classroom__title', 'classroom__code')
    autocomplete_fields = ('classroom',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'classroom', 'starts_at', 'status', 'stream_provider', 'playback_url')
    list_filter = ('status', 'stream_provider')
    search_fields = ('title', 'classroom__title', 'classroom__code')
    autocomplete_fields = ('classroom',)
