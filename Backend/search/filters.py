from django.db.models import Q


def filter_users(queryset, term):
    return queryset.filter(
        Q(username__icontains=term)
        | Q(first_name__icontains=term)
        | Q(last_name__icontains=term)
    )

