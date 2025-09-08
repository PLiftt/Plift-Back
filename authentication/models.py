from django.db import models
import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, role=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        if not password:
            raise ValueError("La contraseña es obligatoria")
        if role is None:
            raise ValueError("El rol es obligatorio")

        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", CustomUser.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        COACH = 'coach', 'Coach'
        ATHLETE = 'athlete', 'Athlete'
        ADMIN = 'admin', 'Admin'

    class Gender(models.TextChoices):
        MALE = 'male', 'Masculino'
        FEMALE = 'female', 'Femenino'
        OTHER = 'other', 'Otro'

    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Nombre")
    second_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Segundo nombre")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Apellido")
    second_last_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="Segundo apellido")
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True, verbose_name="Género")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Fecha de nacimiento")
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.ATHLETE,
        verbose_name="Rol del usuario"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    def _str_(self):
        full_name = f"{self.first_name} {self.second_name or ''} {self.last_name} {self.second_last_name or ''}".strip()
        return f"{self.email} - {full_name} ({self.get_role_display()}, {self.gender}, {self.date_of_birth})"


# Modelo Invitation
class Invitation(models.Model):
    coach = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="invitations_as_coach",
        limit_choices_to={'role': CustomUser.Role.COACH},
        verbose_name="Coach"
    )
    athlete = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitations_as_athlete",
        limit_choices_to={'role': CustomUser.Role.ATHLETE},
        verbose_name="Atleta"
    )
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        status = "Aceptada" if self.accepted else "Pendiente"
        return f"Invitación {self.code} ({status})"