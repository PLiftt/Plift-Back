from rest_framework import serializers
from .models import CustomUser

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
            "role"
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