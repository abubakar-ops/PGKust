from decimal import Decimal

from rest_framework import serializers
from .models import AcademicSession, Programme, Course, CourseAllocation, Timetable, Enrollment, CourseMaterial


class AcademicSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicSession
        fields = ["id", "name", "is_current", "department_fee", "start_date", "end_date"]

    department_fee = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )

    def validate_name(self, value):
        name = value.strip()
        matches = AcademicSession.objects.filter(name__iexact=name)
        if self.instance is not None:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError("An academic session with this name already exists.")
        return name

    def validate(self, data):
        start_date = data.get("start_date", getattr(self.instance, "start_date", None))
        end_date = data.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({"end_date": "End date must be on or after the start date."})
        return data


class ProgrammeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programme
        fields = ["id", "name", "programme_type", "duration_years", "description"]

    def validate_name(self, value):
        name = value.strip()
        matches = Programme.objects.filter(name__iexact=name, programme_type=self.initial_data.get(
            "programme_type", getattr(self.instance, "programme_type", None)
        ))
        if self.instance is not None:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError("A programme with this name and type already exists.")
        return name


class CourseSerializer(serializers.ModelSerializer):
    programme_name = serializers.CharField(source="programme.name", read_only=True)
    credit_units = serializers.IntegerField(min_value=1)

    class Meta:
        model = Course
        fields = ["id", "code", "title", "credit_units", "semester", "programme",
                  "programme_name", "is_elective", "is_active", "description"]

    def validate_code(self, value):
        code = value.strip().upper()
        matches = Course.objects.filter(code__iexact=code)
        if self.instance is not None:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError("A course with this code already exists.")
        return code


class CourseAllocationSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    programme_name = serializers.CharField(source="course.programme.name", read_only=True)
    credit_units = serializers.IntegerField(source="course.credit_units", read_only=True)
    lecturer_name = serializers.SerializerMethodField()
    session_name = serializers.CharField(source="session.name", read_only=True)
    enrolled_count = serializers.SerializerMethodField()
    result_batch_status = serializers.SerializerMethodField()

    class Meta:
        model = CourseAllocation
        fields = ["id", "course", "course_code", "course_title", "credit_units",
                  "programme_name", "lecturer", "lecturer_name", "session", "session_name", "semester",
                  "enrolled_count", "result_batch_status"]

    def get_lecturer_name(self, obj):
        return obj.lecturer.user.get_full_name()

    def get_enrolled_count(self, obj):
        return obj.enrollments.filter(status="APPROVED").count()

    def get_result_batch_status(self, obj):
        from results.models import SemesterResultBatch

        return SemesterResultBatch.objects.filter(
            session_id=obj.session_id,
            semester=obj.semester,
            programme_type=obj.course.programme.programme_type,
        ).values_list("status", flat=True).first()


class AvailableAllocationSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    credit_units = serializers.IntegerField(source="course.credit_units", read_only=True)
    lecturer_name = serializers.SerializerMethodField()
    session_name = serializers.CharField(source="session.name", read_only=True)
    already_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = CourseAllocation
        fields = ["id", "course", "course_code", "course_title", "credit_units",
                  "lecturer", "lecturer_name", "session", "session_name", "semester",
                  "already_enrolled"]

    def get_lecturer_name(self, obj):
        return obj.lecturer.user.get_full_name()

    def get_already_enrolled(self, obj):
        return obj.id in self.context.get("enrolled_allocation_ids", set())


class TimetableSerializer(serializers.ModelSerializer):
    allocation_detail = CourseAllocationSerializer(source="allocation", read_only=True)

    class Meta:
        model = Timetable
        fields = ["id", "allocation", "allocation_detail", "day", "start_time", "end_time", "venue"]

    def validate(self, data):
        if self.instance is not None:
            instance = Timetable(
                pk=self.instance.pk,
                allocation=data.get("allocation", self.instance.allocation),
                day=data.get("day", self.instance.day),
                start_time=data.get("start_time", self.instance.start_time),
                end_time=data.get("end_time", self.instance.end_time),
                venue=data.get("venue", self.instance.venue),
            )
        else:
            instance = Timetable(**data)
        try:
            instance.clean()
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return data


class EnrollmentSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="allocation.course.code", read_only=True)
    course_title = serializers.CharField(source="allocation.course.title", read_only=True)
    credit_units = serializers.IntegerField(source="allocation.course.credit_units", read_only=True)
    lecturer_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    matric_number = serializers.CharField(source="student.matric_number", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "student_name", "matric_number", "allocation", "course_code", "course_title",
                  "credit_units", "lecturer_name", "status", "enrolled_at"]
        read_only_fields = ["id", "student", "status", "enrolled_at"]

    def get_lecturer_name(self, obj):
        return obj.allocation.lecturer.user.get_full_name()

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()


class CourseMaterialSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="allocation.course.code", read_only=True)
    course_title = serializers.CharField(source="allocation.course.title", read_only=True)
    file_available = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = CourseMaterial
        fields = [
            "id", "allocation", "course_code", "course_title", "title", "description",
            "file", "file_available", "can_delete", "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_at", "course_code", "course_title"]

    def get_file_available(self, obj):
        return bool(obj.file and obj.file.storage.exists(obj.file.name))

    def get_can_delete(self, obj):
        lecturer_profile_id = self.context.get("lecturer_profile_id")
        return lecturer_profile_id is not None and obj.uploader_id == lecturer_profile_id
