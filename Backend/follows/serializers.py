from rest_framework import serializers

from accounts.models import User


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name")
        read_only_fields = fields
