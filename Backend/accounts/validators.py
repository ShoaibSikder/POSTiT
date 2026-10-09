from django.core.validators import RegexValidator


validate_public_username = RegexValidator(
    regex=r"^[a-z0-9][a-z0-9._+-]{2,149}$",
    message=(
        "Usernames must be 3-150 characters and use lowercase letters, "
        "numbers, dots, underscores, plus signs, or hyphens."
    ),
)

