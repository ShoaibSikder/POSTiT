from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError


class PostFilterBackend:
    def filter_queryset(self, request, queryset, view):
        term = request.query_params.get("q", "").strip()
        author = request.query_params.get("author", "").strip()
        start = request.query_params.get("from", "")
        end = request.query_params.get("to", "")
        start_date = parse_date(start) if start else None
        end_date = parse_date(end) if end else None
        if start and start_date is None:
            raise ValidationError({"from": "Use an ISO date such as 2026-05-01."})
        if end and end_date is None:
            raise ValidationError({"to": "Use an ISO date such as 2026-05-01."})
        if start_date and end_date and start_date > end_date:
            raise ValidationError({"to": "The end date must be on or after the start date."})
        if term:
            queryset = queryset.filter(content__icontains=term)
        if author:
            queryset = queryset.filter(author__username__iexact=author)
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        return queryset

