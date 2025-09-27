from rest_framework import serializers, permissions, generics
from .models import CustomUser
from .models import Invitation
from training.models import CoachAthlete

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "password",
            "password2",
            "first_name",
            "second_name",
            "last_name",
            "second_last_name",
            "gender",
            "date_of_birth",
            "role",
            "bodyweight_kg",
            "squat_1rm",
            "bench_1rm",
            "deadlift_1rm"
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")  # eliminamos password2 antes de crear el usuario
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            second_name=validated_data.get("second_name", ""),
            last_name=validated_data.get("last_name", ""),
            second_last_name=validated_data.get("second_last_name", ""),
            gender=validated_data.get("gender", None),
            date_of_birth=validated_data.get("date_of_birth", None),
            role=validated_data.get("role")
            
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "second_name",
            "last_name",
            "second_last_name",
            "gender",
            "date_of_birth",
            "role",
            "date_joined"
        ]
        read_only_fields = ["id", "date_joined"]

class InvitationSerializer(serializers.ModelSerializer):
    coach_email = serializers.EmailField(source='coach.email', read_only=True)
    athlete_email = serializers.EmailField(source='athlete.email', read_only=True)

    # Campo de entrada opcional
    athlete = serializers.EmailField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Invitation
        fields = [
            'id',
            'code',
            'coach_email',
            'athlete_email',
            'athlete',   
            'accepted',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'code',
            'coach_email',
            'athlete_email',
            'created_at',
        ]

    def create(self, validated_data):
        coach = self.context["request"].user

        if coach.role != CustomUser.Role.COACH:
            raise serializers.ValidationError({"coach": "Solo los coaches pueden generar códigos."})

        athlete_email = validated_data.pop("athlete", None)
        athlete = None
        if athlete_email:
            athlete_email = athlete_email.strip()
            if athlete_email:
                try:
                    athlete = CustomUser.objects.get(email=athlete_email, role=CustomUser.Role.ATHLETE)
                except CustomUser.DoesNotExist:
                    raise serializers.ValidationError({"athlete": "No existe un atleta con ese email."})

        return Invitation.objects.create(
            coach=coach,
            athlete=athlete,
            **validated_data
        )



class CoachAthleteSerializer(serializers.ModelSerializer):
    coach_email = serializers.CharField(source='coach.email', read_only=True)
    coach_name = serializers.SerializerMethodField()
    athlete_email = serializers.CharField(source='athlete.email', read_only=True)
    athlete_name = serializers.SerializerMethodField()

    class Meta:
        model = CoachAthlete
        fields = [
            'id',
            'coach',
            'coach_email',
            'coach_name',
            'athlete',
            'athlete_email',
            'athlete_name',
            'start_date',
            'end_date'
        ]
        read_only_fields = ['start_date']  # se autoasigna

    def get_coach_name(self, obj):
        return f"{obj.coach.first_name} {obj.coach.last_name}".strip()

    def get_athlete_name(self, obj):
        return f"{obj.athlete.first_name} {obj.athlete.last_name}".strip()