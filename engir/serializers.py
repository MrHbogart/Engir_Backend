from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Classroom, Enrollment, Session, Student, Teacher

User = get_user_model()


class TeacherSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = (
            'id',
            'user_id',
            'full_name',
            'email',
            'headline',
            'bio',
            'profile_url',
            'avatar_url',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at', 'email')

    def get_email(self, obj):
        if obj.user:
            return obj.user.email
        return obj.email


class StudentSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Student
        fields = (
            'id',
            'user_id',
            'full_name',
            'email',
            'bio',
            'interests',
            'timezone',
            'avatar_url',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    teacher_profile = TeacherSerializer(read_only=True)
    student_profile = StudentSerializer(read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'teacher_profile',
            'student_profile',
        )

    def get_role(self, obj):
        if hasattr(obj, 'teacher_profile'):
            return 'teacher'
        if hasattr(obj, 'student_profile'):
            return 'student'
        if obj.is_staff:
            return 'staff'
        return 'guest'


class SessionSummarySerializer(serializers.ModelSerializer):
    is_joinable = serializers.BooleanField(read_only=True)
    is_live = serializers.BooleanField(read_only=True)

    class Meta:
        model = Session
        fields = (
            'id',
            'title',
            'starts_at',
            'ends_at',
            'status',
            'stream_provider',
            'playback_url',
            'host_url',
            'recording_url',
            'is_joinable',
            'is_live',
        )


class ClassroomSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(), source='teacher', write_only=True, required=False
    )
    available_seats = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    next_session = SessionSummarySerializer(read_only=True)

    class Meta:
        model = Classroom
        fields = (
            'id',
            'teacher',
            'teacher_id',
            'title',
            'description',
            'code',
            'starts_at',
            'duration_minutes',
            'capacity',
            'meeting_url',
            'tags',
            'is_public',
            'available_seats',
            'is_full',
            'next_session',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('code', 'created_at', 'updated_at')


class EnrollmentSerializer(serializers.ModelSerializer):
    classroom = ClassroomSerializer(read_only=True)
    classroom_id = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(), source='classroom', write_only=True, required=False
    )
    class_code = serializers.CharField(write_only=True, required=False)
    student = StudentSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            'id',
            'classroom',
            'classroom_id',
            'student',
            'class_code',
            'full_name',
            'email',
            'phone_number',
            'notes',
            'status',
            'source',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, attrs):
        classroom = attrs.get('classroom')
        class_code = attrs.pop('class_code', None)

        if classroom is None and class_code:
            class_code = class_code.upper().strip()
            try:
                classroom = Classroom.objects.get(code=class_code)
            except Classroom.DoesNotExist as exc:
                raise serializers.ValidationError({'class_code': 'Invalid class code.'}) from exc

        if classroom is None:
            raise serializers.ValidationError('Provide classroom_id or class_code to join a class.')

        if classroom.is_full:
            raise serializers.ValidationError({'classroom': 'This class is already full.'})

        attrs['classroom'] = classroom
        return attrs

    def create(self, validated_data):
        classroom = validated_data['classroom']
        email = validated_data['email']
        if Enrollment.objects.filter(classroom=classroom, email=email).exists():
            raise serializers.ValidationError('You are already registered for this class with this email.')
        return super().create(validated_data)


class SessionSerializer(serializers.ModelSerializer):
    classroom = ClassroomSerializer(read_only=True)
    classroom_id = serializers.PrimaryKeyRelatedField(
        queryset=Classroom.objects.all(), source='classroom', write_only=True
    )
    stream_key = serializers.CharField(read_only=True)
    is_joinable = serializers.BooleanField(read_only=True)
    is_live = serializers.BooleanField(read_only=True)

    class Meta:
        model = Session
        fields = (
            'id',
            'classroom',
            'classroom_id',
            'title',
            'description',
            'starts_at',
            'ends_at',
            'duration_minutes',
            'status',
            'stream_provider',
            'stream_key',
            'host_url',
            'playback_url',
            'recording_url',
            'meeting_passcode',
            'is_joinable',
            'is_live',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('stream_key', 'is_joinable', 'is_live', 'created_at', 'updated_at')

    def validate(self, attrs):
        starts_at = attrs.get('starts_at') or getattr(self.instance, 'starts_at', None)
        ends_at = attrs.get('ends_at') or getattr(self.instance, 'ends_at', None)
        if starts_at and ends_at and ends_at <= starts_at:
            raise serializers.ValidationError({'ends_at': 'End time must be after the start time.'})
        return attrs


class AuthTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = (
            'teacher'
            if hasattr(user, 'teacher_profile')
            else 'student'
            if hasattr(user, 'student_profile')
            else 'staff' if user.is_staff else 'guest'
        )
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class TeacherRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=120)
    headline = serializers.CharField(max_length=180, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    profile_url = serializers.URLField(required=False, allow_blank=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        user = User.objects.create_user(username=email, email=email)
        user.set_password(password)
        user.first_name = validated_data.get('full_name', '').split(' ')[0]
        user.save()
        teacher = Teacher.objects.create(user=user, email=email, **validated_data)
        return teacher


class StudentRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=120)
    bio = serializers.CharField(required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    interests = serializers.ListField(child=serializers.CharField(), required=False)
    avatar_url = serializers.URLField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.pop('email')
        interests = validated_data.pop('interests', [])
        user = User.objects.create_user(username=email, email=email)
        user.set_password(password)
        user.first_name = validated_data.get('full_name', '').split(' ')[0]
        user.save()
        student = Student.objects.create(user=user, email=email, interests=interests, **validated_data)
        return student
