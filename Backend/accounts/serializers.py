from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import User
from .validators import validate_public_username


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "date_joined")
        read_only_fields = fields


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "password_confirmation")

    def validate_username(self, value):
        username = value.strip().lower()
        if not username:
            raise serializers.ValidationError("A username is required.")
        try:
            validate_public_username(username)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("This username is already in use.")
        return username

    def validate_email(self, value):
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError("An email address is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("This email address is already in use.")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                {"password_confirmation": "The passwords do not match."}
            )

        candidate = User(username=attrs["username"], email=attrs["email"])
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"password": list(exc.messages)}
            ) from exc
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(trim_whitespace=True)
    password = serializers.CharField(
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        identifier = attrs["identifier"].strip()
        user = User.objects.filter(username__iexact=identifier).first()
        if user is None:
            user = User.objects.filter(email__iexact=identifier).first()

        if user is None:
            raise serializers.ValidationError(
                {"detail": "Invalid username/email or password."}
            )

        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.username,
            password=attrs["password"],
        )
        if authenticated_user is None:
            raise serializers.ValidationError(
                {"detail": "Invalid username/email or password."}
            )

        attrs["user"] = authenticated_user
        return attrs
